** MVP Validation

In order to run our app, type...

python run.py --cli --json

When asked to enter your name, type it in and enter.  You can revisit a profile tied to your name if you ever want to add more tasks

Type and enter '1' to add a task

Enter the task name as "Test1"
Enter the task description as "Testing"
Enter your task category as "Test"

Type and enter '1' again

Enter the task name as "Test2"
Enter the task description as "Testing"
Enter your task categroy as "New Test"

Type and enter '1' one more time

Enter the task name as "Test3"
Enter the task description as "Testing"
-> Notice how you now have two existing categories listed from the cli
Enter your task category as "Test"

Now enter '2' and remove your tasks in the same order that you entered them, based off of ID (you will have to enter '2' three times)
You will see "Task [task_id] removed successfully" each time

Now, with no tasks left, try removing a task again.
You should get "You have no tasks to remove"
In the menu, enter 'e' and exit the application