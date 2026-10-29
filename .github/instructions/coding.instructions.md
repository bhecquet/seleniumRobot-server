

These are general instructions for all coding tasks

# General instructions

- Always write code in english
- Follow best practices for code readability and maintainability


# When developing, 
- only touch the code that is necessary for the task. DO NOT TOUCH the tests.
- Then, execute all unit tests in the module where you wrote your code
- If some test fail, analyze them
  1. If failure is directly related to the code you've written, decide whether you should correct the code or the test. 
  2. If failure is indirectly related to the code, then correct the code, as you may have introduced a regression
- Then reexecute the tests. At the end, all tests should be OK

## How to decide whether new code or test should be corrected

When adding new feature, test may need correction because the new feature changes the expected behavior of the code.
Correct the code if
- the test is still really testing the business rule or the instruction given by the developer
- the failing test is in another module where code has not been touched for this change

Correct the test if
- the test is no longer accurately testing the business rule or the instruction given by the developer