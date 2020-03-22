# Error Wrapper Blender Addon

This is a self-contained proof of concept addon for implementing user error reporting. The idea is, with minimal dependencies, a developer can easily provide users a way to report unexpected issues, while making development management simple.

## Motivation

Some other addons have developed shortcuts for reporting issues in GitHub (or equivalents), however personal experience has found that providing users with max one-click effort level greatly increases the rate at which errors are actually reported. This has two primary benefits:

1) Rarer issues are more likely to be reported with a lower barrier to report. Things like registering for a GitHub account or describing an issue or checking for duplicates may all lead to a report not filed.
2) Higher duplication of common reports. While this may sound like a negative, it helps prioritize errors that are affecting the most users with the most current reports.
3) Helps to confirm issues are resolved. By ensuring that the format of errors are captured consistently, you can detect whether prominent issues were truly resolved by checking that the errors no longer show up in newer releases. Essentially, grades the bug-fixers homework nearly for free!

These are all positive points that have greatly helped personal addon development, and apply for both small and large addons.

## Features

- Error reports are anonymous: It is very transparent to the user what is being submitted, and they technically can intervene to remove any data they don't want sent.
- Simple to implement: You can decorate `execute` functions as-is without changing how code can run. No complicated database setup, as it uses Google Forms & Spreadsheets.
- Non intrusive: Designed to only raise user alerts for truly un-handled exceptions. When it does, it aims to replicate similar to the default Blender error popup but just with the extra report option. Exceptions are still printed to the console for debugging.
- Configurable: Though this designs implements a "backend" using spreadsheets, code could be easily extended as needed for database
- Minimized liability: This builds on top of products (Forms, Spreadsheet) that have their own privacy policy, though you should still make an additive light policy of your own. Also mind the GPL license "as is" clause, be responsible for the data you collect, and know this was not written or vetted by a lawyer.

## High level design

### Within the addon

All operators should be decorated with an error-handling python function (called a wrapper). If an exception occurs, then this triggers a popup operator which allows the user to acknowledge the error and send to the developer (or ignore).

This wrapper is called every time an operators Execute function runs. It passes through the reference to self and the operator context. If the wrapped execute function returns anything like `FINISHED`, `RUNNING_MODAL`, or `CANCELLED`, then it completes without further action.

However when an un-handled exception occurs, the wrapper catches it. It then calls a new operator which contains the popup draw code, and meanwhile returns `{'CANCELLED'}` for the operator the error came from. Cancelled was chosen so that there would not be any duplicate file popups, but it is worth calling out that this also means the operator would not raise an exception if coming from with another operator or script call.

### Within the "backend"

When the user clicks "OK" to report an error, it opens a new window or tab of a webbrowser landing on a pre-filled Google Form. The user then presses submit (after optionally adding more details), which then inserts a new row into the Form-connected Google Spreadsheet. The developer could optionally [enable notifications](https://support.google.com/a/users/answer/9308874?hl=en) for new reports appearing (per new entry or daily summaries).

To call this out: This is a very simple backend, and admittedly not a seamless experience for the user as pressing "OK" and the report already being logged. A more sophisticated example would leverage a custom built public read-only API which passes responses through to a database. Though not terribly difficult to setup, this is an extra barrier to entry for quick and simple user reporting, and requires a different set of skills - hence the focus on this repository is on this low tech but straightforward use of spreadsheets.

## How to setup in your own addon

### 1) Copy the user_reporting.py file into your addon

This contains the mostly pure python code for user reporting. If you wanted to customize for connecting to a database, you would also make these changes here.

### 2) Register the new module and set bl_idname

Edit your addon's `__init__.py` file to import the module and run it's register/unregister functions.

Take note: unlike typical register functions, the `user_reporting.py` register function requires passing in the addon's `bl_info` dictionary. This is used to set the active addon's version so that it is directly logged in the error reports.


*`__init__.py`*

```
from . import user_reporting

def register():
    user_reporting.register(bl_info)

```

### 3) Create a Google form

Now we jump over to creating a google form, which later we connect the questions fields to the Blender addon.

Most likely, these are the key fields your Google Form should have:
- Addon Version
- Blender Version
- Platform (operating system)
- Error Message
- Optional (default blank) field for more information

The exact names do not matter, just make sure one field exists for each of the above. It does not hurt to add more, if appropriate.

Key note: Deleting a field is NOT a good idea unless really needed. As you will see in the next step, each question gets a unique ID. Re-ordering, renaming, etc is all fine, but don't delete a question once you start using it in production unless you are sure you never want it back. Deleting and adding questions doesn't break the form itself in any way, it just severs the link to the blender addon so it is no longer automatically filled out when the page is opened from Blender.

See the [live form](https://docs.google.com/forms/d/e/1FAIpQLSdHTA6aOJCbNsTCpRoWDWheWuQjci1d6gxnxHb1FdAnXvRHdw/viewform) used in this repository's example, noting the one optional question added and the arbitrary question order.

### 4) Generate a pre-filled form link

In order for this system to work, we need to deep link the user into a form that already fills out all of the required questions. To do this, we need to get the backend field IDs for each question.

The the convenient way to get these unique IDs is by generating a "prefilled link", and extracting the IDs from there. To make it easy, consider entering the plain lower case, no-spaces name of each question into the fields you want to pre-populate. Example below

Example pre-filled form output (test it out in a new window!):

```
https://docs.google.com/forms/d/e/1FAIpQLSdHTA6aOJCbNsTCpRoWDWheWuQjci1d6gxnxHb1FdAnXvRHdw/viewform?usp=pp_url&entry.391369946=addon_version&entry.1215866813=blender_version&entry.1023948975=error_message&entry.286196237=platform
```


### 5) Update global variables in `user_reporting.py`

Update each of the following three areas:

1) `IDNAME` should just be a unique, lowercase prefix to use in the report popup operator's `bl_idname`.

2) `FORM_ID` should be set to Google Form's ID. For example, `1FAIpQLSdHTA6aOJCbNsTCpRoWDWheWuQjci1d6gxnxHb1FdAnXvRHdw` is the ID you would get from the sample link above. Be sure the grab the ID from the actual prefilled link, and note it does not include any slashes.

3) `FORM_FIELDS`, which maps individual question IDs in the form with the value we populate from Blender.

From the prefilled url in the previous step, we can see `entry.1215866813=blender_version` is one of the encoded parameters. In this case, `blender_version` was manually typed into the question which was named "Blender Version". In the URL, this "Blender Version" question is represented with the ID `entry.1215866813`. Thus, the blender_version key should be listed as `1215866813` in `user_reporting.py` file (ignore the `entry.` part). Replace all IDs found in the `FORM_FIELDS` accordingly.

You can add more if you like, but this only makes sense if you think you can prefill the values of the given field inside blender. Any fields requiring manual user entry can be ignored in the URLs the addon generates.


### 5b) [Optional, more advanced] Async integration to submit to form instead of open link

Just to call this out, if you want to make the process even more seamless, you could directly log the data into a spreadsheet instead of using Forms as a middle-man.

Caution: This would require generating a Google API key for spreadsheets, and this would be public in your addon (and thus potentially abused). If you're going down this route, consider taking it a step further and actually integrate with a live database service instead of forms, but that's your own call.

### 6) Decorate all execute functions

Now add function decorators to every operator function you want to have user error reporting. Or at least the ones you want user reporting for, though there's no particular reason why you would not use it for all operators your addon defines.

This is done using the `@user_reporting.wrapper` decorator around the execute function. Full example below.

*File where operator is defined*
```
from . import user_reporting

...

class URW_OT_no_error(bpy.types.Operator):
    """An operator which has no errors"""
    bl_idname = "object.userreport_no_error"
    bl_label = "Demo No Error"

    @user_reporting.wrapper
    def execute(self, context):
        return {'FINISHED'}
```

### 7) Test it!

Force an operator to fail by throwing an `Exception` in one of the decorated execute functions of an operator. When next running this operator, you should get a popup. On pressing OK, as browser page should open with questions prefilled.

Not working? Some troubleshooting steps:

- I am not getting a popup: Make sure your addon operator is raising an intentional exception, and that the execute function (not draw function or anything else) was properly added. Try restarting blender to fully reload the python modules, as a simple in-session refresh may not work.
- A browser window is not opening when I press OK: There may be an error happening in the decorator code, double check your blender console to find out what.
- A browser window opens, but shows a broken link ("resource unavailable): Double check to make sure you updated the correct form id. Start with a working (prefilled) link, grab the ID from this. Do not grab the ID from the "edit form" url.
- The form loads, but none or only some of the auto-filled questions are actually auto-filled: Double check the question IDs coming from the prefilled link. This is also a good place to reiterate: deleting questions will remove the question's ID, which cannot be undone.

### 8) (Optional) Add direct reporting function

If you want, you can also add buttons to panels or menus to directly open the reporting Form in a browser. This being said, this would require a user to fill out "error" section of the form, which then won't be in the same format as normal traceback errors like other issues, but is a way to put it all in one place. They still get their blender version, addon version, and platform auto filled out.

To use this, use the sample below in a panel or menu draw function.

```
# directly open form in browser, prefilling all but the error message field
ops = col.operator("wm.url_open", text="Report error")
ops.url = user_reporting.Reporter.default_form_url
```

### 9) Reporting and analysis

This section is a bit looser as there is any number of ways to then manager the stream of reports coming through. Some key suggestions though:

- Add a custom column to the right of the raw form answers, which reduces all errors to just the last e.g. 64 characters via a formula. Add another column to the right after that which counts the number of times this consolidated error message appears, to help give weight to the most common errors.
- Build a pivot table off of the raw data, and pivot by version number or count of errors (again, the "consolidated" error is helpful here to group things together)
- Keep the raw data the raw data, import the responses elsewhere if you need to transform the values more significantly or it gets to be too large and slow to load.

See [this sample spreadsheet](https://docs.google.com/spreadsheets/d/1Lg_h1Mxl38BeDXoKKw5-twIKluKN89rxPpnpWfgmXgs/) showing some of these basic layers of analysis, including custom formulas. The key themes of analysis is to group similar error reports or users, and help prioritize the most impacted users. In this sense, there are a couple good ways to pivot the data to view the situation:'

- Pivot by error reports: Will show the most common error reports
- Pivot by platform: You can see which operating system reports more errors; maybe you develop on one OS, and users of another keep running into path-based issues?
- Pivot by version: Either blender version or addon version. Check your homework that you actually fixed prior errors by seeing they don't pop up in newer versions of your addon!


## Further thoughts

The above workflow is the tip of the iceberg of what is possible, but hopefully demonstrates that it does not need to be complex in order to be useful. Some thoughts on extensions:

- Replace the Google Form interface with a direct API call to submit the report, thus avoiding the user from ever leaving blender (any friction will result in a loss of responses!). See the [MCprep addon](https://github.com/TheDuckCow/MCprep), which uses the Firebase realtime database for this purpose. Be sure to make put your internet calls inside an asynchronous thread!
- Detect whether a user's error has been reported before, or even solved.
  - To do this, consider making a hash of the error report and then reading from a published place a list of reported or solved errors. This could even be the same spreadsheet that raw errors are reported to, although that would require making that entire spreadsheet publicly viewable. Better would be to make another public read-only spreadsheet that imports only the precomputed hash and then whatever supporting information for the given bug report hash (canonical issue links, fix status, etc)
  - Can direct the user to install the latest version, or even redirect them to a thread with more details on the issue (e.g. a canonical issue thread)
- Weird bonus: Auto detect if a new version of the addon is out, simply by querying whether bug reports from a newer version exist! (OK, but really this is what features like the Addon Updater module are for)

