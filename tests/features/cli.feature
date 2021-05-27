Feature: CLI

        The command line tool is used to extract data from Jira,
        supplement it with Kanban attributes, and export it
        in a format that is ingestible by a data analysis or
        visualization tool.

        The minimal parameters for the command line tool are:
        * one or more Jira project names
        * a "start date" for when data is extracted

        The optional parameters are:
        * an "end date"
        * a username
        * the API token associated with the username
        * a selection type which can be one of "created" or "modified"

    exit code 0 == success
    exit code 2 == invalid usage

    Scenario: Application displays correct version
        Given the cli is runnable
        When the cli is invoked with the version flag
        Then the version is displayed on stdout
        And the application ends with an exit code of 0

    Scenario: Application terminates successfully if there are no projects
        Given the cli is runnable
        When the cli is invoked with no projects
        Then the application ends with an exit code of 0

    Scenario: From-date is required
        Given the cli is runnable
        When the cli is invoked with no from date
        Then the application has an error message with: Missing option '--start-date'
        And the application ends with an exit code of 2
