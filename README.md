# cpsc471-intermurals
API for managing intramurals basketball league. 


Setting up enviroment in Windows :(

1. Install pip for windows command line. I think it comes with python3.

2. Create project folder. Pull repository.

3. Create a virtual enviroment for the project.
  Run in Windows command prompt (probably in admin mode):
    >python3 -m venv env
  
    This should've created a env\ directory with Include\ Lib\ Scripts\ .
    Start the virtual enviroment, run:
    >env\Scripts\activate
    
    If everything is going according to plan (env) should be showing at the start of the new command.


LINUX: virtualenv venv //names the environment (venv)


4. Set enviroment variable.

    Navigate to edit system variables (use windows search).
    Under user variables add new:
    
    >Variable name: APP_SETTINGS
      
    >Variable value: config.DevelopmentConfig
      
    Since database credentials shouldn't be in a git repo, we will store them in enviroment variables. 
    
    Add following 4 variables and corresponding value:
  
    >MYSQL_DB
      
    >MYSQL_HOST
      
    >MYSQL_PASSWORD
      
    >MYSQL_USER
  
    Make sure to restart your windows command prompt app, otherwise variables won't work.

LINUX: start virtual environment ($source venv/bin/activate)
	call the bash script ($source ./activate.sh)

LINUX: Check environment variables ($printenv)

5. Install needed tools.
  Run pip installer tool against requirements.txt:
    >pip install -r requirements.txt

6. Check that it works locally:
    >python3 run.py

LINUX: close virtual environment ($deactivate)


