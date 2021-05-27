"""Parses Jira issues and enriches the result with derived Kanban attributes."""
from dataclasses import dataclass, field
import datetime
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar

from dateutil.parser import parse as parse_date


@dataclass(frozen=True)
class User:
    """Represents a Jira user.

    Users appear as assignee, reporter, and creator of Jiras

    Attributes:
        name: the full name (display name) of the user
        email: the email address. This is a unique identifier
    """

    name: str
    email: str


@dataclass(frozen=True)
class State:
    """Represents the state of the Jira at this point in time.

    The state of the Jira depends on the workflow and is mapped from
    the Jira status. The value is normalized to lower case.

    The category is one of ``optional``, ``committed``, and ``delivered``. Each category
    has different ways that work is handled. Optional work is work that the team
    hasn't committed to doing and can be discarded -- in fact, it's a sign of
    organizational maturity to have optional work discarded if the requestor learns
    that it doens't provide enough value to be worth implementing.

    When work moves to the ``committed`` phase, the service delivery team is committing
    to delivering the work. It doesn't necessarily mean that the work has started, just
    that it will be delivered. This is the point where the clock starts for
    determining the lead time.

    Finally, ``delivered`` means that the work has been accepted by the requestor.
    This is the point where metrics like lead time and delivery rate can
    be calculated.

    Attributes:
        name: the value of the status attribute of the Jira.
            This will be normalized to lower case.
        category: this value is derived based on the location of the work in the workflow.
    """

    name: str
    category: str


@dataclass(frozen=True)
class Event:
    """This represents a transition from one state to another.

    Attributes:
        state: the new state of the issue
        changed_on: the timestamp on which the change occurred
        agent: the ``User`` who istigated the change
    """

    state: State
    changed_on: datetime.datetime
    agent: User


@dataclass(frozen=True)
class WorkItem:
    """The dataclass that represents the Jira issue.

    Attributes:
        key: the key used to identify the issue, e.g., (``XYZZY-1``)
        summary: the summary field from the Jira
        requested_by: the ``User`` who initiated the request
        assigned_to: the ``User`` to whom the issue has been assigned. Can be ``None``.
        contributors: a collection of users who are working on the issue.
            This is a custom field in Jira.
        class_of_service: Used for prioritization based on cost of delay.
            This is derived from Priority.
        events: a collection of status changes made to the Jira in chronological order
        created_on: the timestamp of when the issue was created
        last_modified: the timestamp of the last modification date.
        is_done: indicates if the work has been delivered
        lead_time: total calendar days elapsed between commitment and delivery inclusive
        commitment_point: the point in the workflow where work shifted
            from ``optional`` to ``committed``.
        accepted_on: the timestamp of when the work was identified as potentially committable
        committed_on: the timestamp of when the work was committed to. This is the starting
            point for the lead time calculation.
        delivered_on: the timestamp for when the work was delivered. This is the end point
            for the lead time calculation.
    """

    key: str
    summary: str
    requested_by: User
    assigned_to: Optional[User]
    contributors: Optional[List[str]]
    class_of_service: str
    events: List[Event]
    current_state: State
    created_on: datetime.datetime
    last_modified: datetime.datetime
    # Derived fields below
    is_done: Optional[bool] = field(init=False)
    lead_time: Optional[int] = None
    commitment_point: Optional[str] = None
    accepted_on: Optional[datetime.datetime] = None
    committed_on: Optional[datetime.datetime] = None
    delivered_on: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        """Adds values for the derived fields."""
        self._thawed_setattr("is_done", self.current_state.name == "done")
        commitment = _determine_commitment(self.events)
        acceptance = _find_first(partial(is_state, state="accepted"), self.events)
        if acceptance:
            self._thawed_setattr("accepted_on", acceptance.changed_on)
        if commitment:
            self._thawed_setattr("commitment_point", commitment[0])
            self._thawed_setattr("committed_on", commitment[1])
        if self.is_done:
            deliver_event = _unbox(
                _find_first(partial(is_state, state="done"), self.events)
            )
            self._thawed_setattr("delivered_on", deliver_event.changed_on)
            self._thawed_setattr("lead_time", _calculate_lead_time(self.events))

    def _thawed_setattr(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)  # getting around frozen state


T = TypeVar("T")
UnaryPredicate = Callable[[T], bool]

# TODO: Make this dynamic so it supports different workflows


def _resolve_category(state: str) -> str:
    """Determines the category of the workflow state."""

    if state in ("requested", "accepted"):
        return "optional"
    elif state in ("done", "not delivered"):
        return "delivered"
    return "committed"


def _determine_commitment(
    events: Sequence[Event],
) -> Optional[Tuple[State, datetime.datetime]]:
    """Determines the commitment point for the work.

    Ideally, the commitment point is the "leftmost" point in the workflow where
    the team commits to doing the work. Often this is a buffer called something like
    "up next" but it could also be where the team actually starts planning or doing
    the work. Understanding where the commitment point occurs helps identify potential
    problems with the workflow.

    For example, issues that are delivered but don't have a commitment point is a sign that
    people are doing the work and creating a Jira after the work is complete. Issues that are
    created and move directly into a "doing" state indicates that replenishment and
    prioritization are being skipped. This may not be a bad thing -- you'd expect to see
    this behavior with critical defects, for example, but may be a symptom of other problems.

    Args:
        events: the sequence of events to inspect for the commitment point

    Returns:
        a tuple with the state where the commitment occurred and the timestamp
          of commitment. If no commitment point can be found, ``None`` is returned.
    """
    for event in events:
        if _resolve_category(event.state.name) == "committed":
            return (event.state, event.changed_on)
    return None


def is_state(event: Event, state: str) -> bool:
    """Determines if the event corresponds to a state or some other event type."""
    return event.state.name == state


def _calculate_lead_time(events: Sequence[Event]) -> int:
    """Calculates the lead time as the number of days between commitment and delivery."""
    start = _find_first(partial(is_state, state="up next"), events)
    end = _find_first(partial(is_state, state="done"), events)
    if start is None or end is None:
        raise ValueError(
            f"start and end are needed for lead time calculation: {start}, {end}"
        )
    start_actual: Event = start  # needed for mypy
    end_actual: Event = end
    return _calculate_interval(end_actual, start_actual)


def _find_first(pred: UnaryPredicate, lst: Sequence[T]) -> Optional[T]:
    """Finds the first element in a sequence that matches the predicate."""
    for elt in lst:
        if pred(elt):
            return elt
    return None


def _calculate_interval(start: Event, end: Event) -> int:
    """Calculates the interval in days inclusive between two events."""
    return abs((end.changed_on - start.changed_on).days) + 1


def parse_issue(issue: Dict[str, Any]) -> WorkItem:
    """Parses a Jira issue into a ``WorkItem``.

    The ``WorkItem`` consists of a stripped-down "Kanban-centric" view of the
    Jira issue. It contains a mix of values from the issue as well as some
    derived attributes.

    Args:
        issue: the python-parsed JSON response from the Jira REST API

    Returns:
        a ``WorkItem`` that contains the relevant Jira data and other
          additional derived attributes needed for Kanban analysis.

    """
    key: str = issue["key"]
    fields: Dict[str, Any] = issue["fields"]
    summary: str = fields["summary"]
    requested_by = _unbox(_extract_user(fields["creator"]))
    assigned_to = _extract_user(fields["assignee"])
    class_of_service = fields["priority"]["name"]
    current_state = _extract_state(fields["status"])
    created_on = parse_date(fields["created"])
    last_modified = parse_date(fields["updated"])

    events = [
        Event(
            state=State(name="requested", category="optional"),
            agent=requested_by,
            changed_on=created_on,
        )
    ]
    changelog = issue["changelog"]["histories"]
    events.extend(
        [_extract_workflow_event(e) for e in changelog if _is_workflow_event(e)]
    )

    return WorkItem(
        key=key,
        summary=summary,
        requested_by=requested_by,
        assigned_to=assigned_to,
        class_of_service=class_of_service,
        contributors=None,
        events=sorted(events, key=lambda e: e.changed_on),
        current_state=current_state,
        created_on=created_on,
        last_modified=last_modified,
    )


def _extract_user(user: Optional[Dict[str, str]]) -> Optional[User]:
    """Extracts the user data from the Jira issue."""
    if user is None:
        return None
    return User(name=user["displayName"], email=user["emailAddress"])


def _unbox(val: Optional[T]) -> T:
    """Safely converts an ``Optional[T]`` into a ``T``.

    This allows for type-safe conversions where there may be missing
    data. It should be used where raising an exception is the
    right thing to do if the value is missing.

    (The "box" is metaphorical, since the ``Optional`` is really
    a ``Union`` type of ``None`` and ``T``. This function just
    narrows the type to ``T``.)

    Args:
        val: an ``Optional`` of some type ``T``

    Returns:
        the "unboxed" val

    Raises:
        ValueError if ``val`` is ``None``.
    """
    if val is None:
        raise ValueError("Nothing to unbox")
    return val


def _extract_state(status: Dict[str, Any]) -> State:
    """Extracts the current state of the issue."""
    status_name: str = status["name"].lower()
    return State(
        name=status_name,
        category=_resolve_category(status_name),
    )


def _extract_workflow_event(event: Dict[str, Any]) -> Event:
    """Extracts an event from the issue."""
    workflow_state = _extract_workflow_state(event)
    agent = _unbox(_extract_user(event["author"]))
    changed_on = parse_date(event["created"])
    return Event(
        state=State(name=workflow_state, category=_resolve_category(workflow_state)),
        changed_on=changed_on,
        agent=agent,
    )


def _is_workflow_event(event: Dict[str, Any]) -> bool:
    """Determines if the event is a workflow event.

    Jira events are any change to the issue and they all show up in the
    issue ``histories`` object. This function is used to separate out
    workflow events (which we care about) from other changes.

    Args:
        event: the JSON data structure containing the event

    Returns:
        a boolean indicating if this is a workflow event
    """
    if "items" not in event or len(event["items"]) == 0:
        return False
    for item in event["items"]:
        if item.get("field") == "status":
            return True
    return False


def _extract_workflow_state(event: Dict[str, Any]) -> str:
    """Extracts the workflow state.

    Args:
        event: the event containing the status

    Returns:
        the string representing the workflow state

    Raises:
        ValueError: when the event isn't a workflow event
    """
    for item in event["items"]:
        if item["field"] == "status":
            return item["toString"].lower()
    raise ValueError(f"Not a workflow event: {event}")
