# photomosaic-bdds

## setup
Add required environment variables
```bash
export BEHAVE_USERNAME={SOME_USERNAME}
export BEHAVE_EMAIL={SOME_EMAIL}
export BEHAVE_PASSWORD={SOME_PASSWORD}
```

# install

requires nose and behave
`pip3 install -r requirements.txt`

# Add tests

Create a new `some_feature.feature` file in `features`
Create step definitions in `features/steps/steps.py`

# Usage
Spin up the photomosaic stack
From root directory enter: 
```bash
behave
```
