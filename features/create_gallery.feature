Feature: As a user I want to make a photomosaic
  Background:
    Given A user named "Behave_Test" does not exist

  Scenario Outline: A new image is uploaded
    Given I can login to an account <username>
    When I upload a new file <image_file>
    Then The status should be ok
    And The thumbnail and image should be accessible

    Examples: Images
    |username   | image_file|
    |Behave_Test|data/chuck.jpg     |
    |Behave_Test|data/ships.gif     |

    Scenario Outline: A gallery item is created
      Given I can login to an account <username>
      And I upload a new file <image_file>
      When I send a new message with enlargement <enlargement> and tile_size <size>
      Then I can poll the pending endpoint until the job completes
      And Verify the resulting gallery against <image_file>

      Examples: Gallery Info
      | username  | image_file   | enlargement | size |
      |Behave_Test|data/chuck.jpg|1            |8     |
      |Behave_Test|data/chuck.jpg|3            |8     |
      |Behave_Test|data/ships.gif|1            |8     |
      |Behave_Test|data/ships.gif|3            |8     |
