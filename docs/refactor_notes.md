** Refactor Notes

In order to align more with SOLID principles, we made various changes to our code in order to refactor it.

*** 1. Instead of CLI integration, our project structure has been updated to accomodate database functionality.  This functionality will be foundational to our final product.

*** 2. Principles of MVC have been maintained for this project.  For example, "Orchestrator" is a class that acts primarily as a controller for the rest of our app.  All other classes are highly specialized Module classes that assist our controller classes.  Our "View" classes are given to add the UI wrapper over our Module and Controller classes.

*** 3. The principle of single responsibility has been maintained.  Each class that we have serves one particular purpose, such as logging in users or routing user input.  We have avoided creating massive "Superclasses" that act as big containers rather than actual programming tools.  Instead, we have maintained high cohesion in our classes and made it so that they are useful units of code.

*** 4. The Open/Closed principle has been maintained.  For example, in our database integration, we did not delete or modify our existing CLI code.  Instead, we created new code to reroute the flow of information to our databases, and the user can still use the CLI if they so wish, since none of that code has been modified or deleted.

*** 5. The Liskov Substitution principle has been maintained, since all subclasses are substitutable for base classes, and they don't break the behavior of our code.

*** 6. The Interface Segregation principle has been maintained.  There are no classes that force users to depend on methods that they don't use.  For example, we separated our CLI and database integration for this purpose.

*** 7. We have been working on the Dependency Inversion principle to ensure that the flow of information is based off of abstractions instead of low-level modules.

*** 8. We have made our classes so that they have low coupling.  Each class can perform a certain function on its own with minimal dependencies.