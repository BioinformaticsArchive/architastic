Installation:

  1. Download the recent stable source version of web2py from http://www.web2py.com/examples/default/download

  2. unzip

  3. make a link called web2py/applications/achitastic that points to the top of your local version of this git repo (the achitastic directory)

  4. from the top of the web2py dir you should be able to run

 	$ python web2py --nogui

   Enter the password that will be the admin of the web server

  5. You should then see the server at:

  	http://127.0.0.1:8000/architastic

  6. To restart the server with the same password, use:

  	$  python web2py.py --nogui -a '<recycle>'