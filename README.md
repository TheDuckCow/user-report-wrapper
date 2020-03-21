# Error Wrapper Blender Addon

This is a self-contained proof of concept addon for implementing user error reporting. The idea is, with minimal dependencies, a developer can easily provide users a way to report unexpected issues, while making development management simple.

## Motivation

Some other addons have developed shortcuts for reporting issues in GitHub (or equivalents), however personal experience has found that providing users with max one-click effort level greatly increases the rate at which errors are actually reported. This has two primary benefits:

1) Rarer issues are more likely to be reported with a lower barrier to report. Things like registering for a GitHub account or describing an issue or checking for duplicates may all lead to a report not filed.
2) Higher duplication of common reports. While this may sound like a negative, it helps prioritize errors that are affecting the most users with the most current reports.
3) Helps to confirm issues are resolved. By ensuring that the format of errors are captured consistently, you can detect whether prominent issues were truly resolved by checking that the errors no longer show up in newer releases. Essentially, grades the bug-fixers homework nearly for free!

These are all positive points that have greatly helped personal addon development, and apply for both small and large addons.

## Features

- Error reports are anonymous
- Minimal change to existing addons: You can decorate `execute` functions as-is without changing how code can run
- Non intrusive: Designed to only raise user alerts if an exception has occurred, and when it does aims to show the same information the user would ordinarily see (ie the error message)
- Does not obfuscate development: Exceptions are still printed out to the console, and users still get a popup which they can screen shot for further help.
- Functions off of Google Spreadsheets for ease of use, but easily configured for other endpoints such as dedicated database endpoints
- User reports are handled in a background thread
- (TODO): Duplicate error reports are

## High level design

All operators should be decorated with an error-handling python function (called a wrapper). If an exception occurs, then this triggers a popup operator which allows the user to acknowledge the error and send to the developer (or ignore).

This wrapper is called every time an operators Execute function runs. It passes through the reference to self and the operator context. If the wrapped execute function returns anything like `FINISHED`, `RUNNING_MODAL`, or `CANCELLED`, then it completes without further action.

However, if the function returns `ERROR` (optionally) or has an un-handled exception (most common coverage), it captures the original error and passes this to a new popup operator which will let the user report the issue.

## How to setup in your own addon

### 1) Copy the user_reporting.py file

This contains the mostly pure python code for user reporting

TODO: Consider enabling some sort of pip install as well.

### 2) Register the new module and set bl_idname


### 3) Use the error reporting wrapper


### 4) Create a Google form

Most likely, these are the core fields your google form should have:
- Addon Version
- Blender Version
- Platform (operating system)
- Error Message
- Optional (default blank) field for more information

The exact names do not matter, just make sure one field exists for each of the above, and add more if appropriate.

### 5) Generate a pre-filled link

In order for this sytem to work, we need to deep link the user into a form that already fills out all of the required details. To do this, we need to get the backend field IDs that forms has for each question.

The the convenient way to get these unique ids for each question is by generated a "prefilled link", and extracting the IDs from there. To make it easy for yourself, consider entering the plain lower case, no-spaces name of each question into the fields you want to pre-populate. Example below

![alt](images/form_prefill.png)

Example pre-filled form output (test it out!):

```
https://docs.google.com/forms/d/e/1FAIpQLSdHTA6aOJCbNsTCpRoWDWheWuQjci1d6gxnxHb1FdAnXvRHdw/viewform?usp=pp_url&entry.391369946=addon_version&entry.1215866813=blender_version&entry.1023948975=error_message&entry.286196237=platform
```


### 6) Update FORM_FIELDS ids with the ids from pre-filled link

For instance, from the url above we can see `entry.1215866813=blender_version`, where `blender_version` is what was manually typed into the question for the Blender Version. Thus, the blender_version key should be listed as `1215866813` in user_reporting.py file. Replace all IDs found in the `FORM_FIELDS` accordingly.

You can add more if you like, but this only makes sense if you think you can prefill the values of the given field - any fields requiring user entry can be left blank and ignored in the URLs the addon generates.


### 6b) [Optional, more advanced] Async integration to submit to form instead of open link

Just to call this out, if you want to make the process even more seamless, you could directly log the data into a spreadsheet instead of using Forms as a middle-man.

Caution: This would require generating a Google API key for spreadsheets, and this would be public in your addon (and thus potentially abused). If you're going down this route, consider taking it a step further and actually integrate with a live database service instead of forms, but that's your own call. More [info here](https://stackoverflow.com/questions/46583052/http-google-sheets-api-v4-how-to-access-without-oauth-2-0/46583300) on connecting to spreadsheets programatically.

### 7) Decorate all execute functions

Or at least, all functions you want to enable reporting for.

### 8) Test it!

Force an operator to fail by throwing an execution with the wrapper enabled, and see it how it responds. You should get a popup, and

### 9) Reporting and analysis

This section is a bit looser as there is any number of ways to then manager the stream of reports coming through. Some key suggestions though:

- Make use of pivot tables
- Keep the raw data the raw data, import the responses elsewhere if you need to transfer (e.g. to identify which issues have been resolved)

See this sample spreadsheet that shows an analysis layer. The key things this spreadsheet does is actually identify similar error reports, so that the developer can visually sort by the most frequent reports in a quick and simple fashion.


## Further thoughts

The above workflow is the tip of the iceberg of what is possible, but hopefully demonstrates that it does not need to be complex in order to be useful. Some thoughts on extensions:

- Replace the Google Form interface with a direct API call to submit the report, thus avoiding the user from ever leaving blender (any friction will result in a loss of responses!). See the MCprep addon, which uses the Firebase realtime database for this purpose. Be sure to make put your internet calls inside an asynchronous thread!
- Detect whether a user's error has been reported before, or even solved.
  - To do this, consider making a hash of the error report and then reading from a published place a list of reported or solved errors. This could even be the same spreadsheet that raw errors are reported to, although that would require making that entire spreadsheet publicly viewable. Better would be to make another public read-only spreadsheet that imports only the precomputed hash and then whatever supporting information for the given bug report hash (canonical issue links, fix status, etc)
  - Can direct the user to install the latest version, or even redirect them to a thread with more details on the issue (e.g. a canonical issue thread)
- Weird bonus: Auto detect if a new version of the addon is out, simply by querying whether bug reports from a newer version exist! (OK, but really this is what features like the Addon Updater module are for)

