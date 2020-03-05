# Spike detection

The spike detector is run after every tool execution. Assuming the tool is compliant (produces a control metric file) it acts as a first line of defense against anomalous data.

The current method of detection is to compare the current value of the control metric with the average of the last 2 values, and produce a notification entry if the difference is more than 6%.

As such it is recommended that the control metric be something that is not very volatile and subject to abrupt changes.

Notification entries are picked up by the notification listener, a job that is automatically spawned when the scheduler starts. At this stage the notifications are logged but not acted upon.
