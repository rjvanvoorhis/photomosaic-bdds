Feature: As a user I want to make an account
  Background:
    Given A user named "Behave_Test" does not exist

  Scenario: A new account is created
    Given A new account has just been created with username "Behave_Test" and email "photomosaic.api@gmail.com"
    Then The status should be ok
    And An email should have been sent

  Scenario:
    Given A new account has just been created with username "Behave_Test" and email "photomosaic.api@gmail.com"
    When I attempt to login as "Behave_Test" I am stopped for not being validated
    Then I validate the user "Behave_Test"
    Then The status should be ok
    And I can login to the account with username "Behave_Test"