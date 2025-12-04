**Singleton Design Pattern - Used**

We want to use the Singleton Design pattern to create our calendar implementation and our home page implementation.  Although we are using primarily frontend language (JS React) to do this, we want each module to return one div object that gets appended to and edited continually, rather than creating new instances of it over and over again.

This design pattern is being implemented to help the live page perform in a flexible manner.  We don't want messy code that creates uneeded instances of frontend structures.

This Design Pattern implementation will be implemented to follow SOLID principles and reduce dependencies whenever possible.  Porter and Kaiden will primarily be responsible for this when creating the calendar.

See the \frontend\calendar\compose for our implementation.

**Decorator Design Pattern - Unused**

We thought it would be useful to implement the decorator design pattern into our User and Task code.  That way, we could apply due dates, task lists, and other attributes to a task as external decorator classes.  This would further organize our code and make it more modular.  However, due to time constraints and a limited bandwidth used to finish other features, we didn't get around to it.  Additionally, our code is already very functional and modular with the way it is now.  It wouldn't make sense to implement it, considering that we'd have to violate the OCP in order to refactor our old code.

**Factory Design Pattern - Unused/Already Applied**

We originally considered implmenting the Factory DP because we could use it to create more controller classes to assemble objects from other module classes.  We thought it would be good to implement it in order to process task data, but we realized that our orchestrator class in the backend achieves this purpose.  Our orchestrator class takes data from other Task and User-related classes, and it processes it in a way that other classes can use.  The same principle applies to our API classes that process external information.  Overall, it wouldn't make sense to implement this pattern because the changes to our code would cause minimal improvements that wouldn't be worth it in the long run.  We already have the general idea of this DP applied, so there's no incentive to mess with our code base further.
