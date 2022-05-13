###pyCRMlite-CGI

pyCRMlite-CGI is just a Python example implementing a simple backend web application including
a set of common artifacts which can be found in many web applications: static web 
pages, templates which are rendered with data collected from a database, graphs 
generated from data in the database, etc.

The specific aspect of this project is that 'standard' CGI are used for its
implementation.

As this repository includes other projects where the same web application is 
implemented using other frameworks, they can be used to compare them and to analyze
implications from the point of view of the development process, and even performances.

It is not included information for deploying the application in a production 
environment, but the following layout and configuration has been used with the Apache2 server where
this application:
- Apache2 default configuration files without modification
- web pages and artifacts in the static directory of the project has been placed in /var/www/html
- python scripts in /usr/lib/cgi-bin
- templates in /usr/lib/cgi-bin/templates
- database in /var/lib/crmlite

All files shall have the adequate permissions to allow web server access them.

Full Doxygen html documentation can be found in the doc directory.


