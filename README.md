# timelapse-pics

Script for taking photos with given interval.  
Few configuration options are available:
- possibility of choosing camera from mounted ones
- defining max disk space which can be used
- defining images resolution
- choosing location for taken pictures
- defining interval

### Running

#### Running with Virtualenv
1. Create virtualenv `virtualenv venv`
2. Activate virtualenv `source venv/bin/activate`
3. Install dependencies `pip install -r requirements.txt`
4. Run script `./run.sh` (or better `./run.sh --help`)
5. Deactivate virtualenv `deactivate`

#### Running without Virtualenv
1. Install dependencies `pip install -r requirements.txt`
2. Run script `./run.py` (or better `./run.py --help`)

