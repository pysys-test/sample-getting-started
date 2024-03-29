import sys
import os
import json
import logging
import urllib.request

import pysys.basetest, pysys.mappers

class MyServerHelper:
	""" A mix-in class providing functionality related to "MyServer" in a test field called ``self.myserver``. 

	To use this just inherit from it in your test, but be sure to leave the BaseTest as the last class, for example::

		from myorg.myhelper import MyServerHelper
		class PySysTest(MyServerHelper, pysys.basetest.BaseTest):
	
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs) # MUST start by calling super implementations
		self.myserver = MyServerHelper.MyServerHelperImpl(self)
		""" Provides access to a set of helper methods for configuring and starting MyServer instances. """
		
	HELPER_MIXIN_FIELD_NAME = 'myserver' # Best practice is to set this field to inform PySys that this class adds a field of this name to the base test class
	# NB: Do NOT add ANY extra methods/fields to the helper itself - all functionality must be safely encapsulated within the nested Impl class. 

	class MyServerHelperImpl(object):
		def __init__(self, testObj: pysys.basetest.BaseTest):
			self.owner = testObj
			self.log = logging.getLogger('pysys.myorg.MyServerHelper')
			# NB: could call self.owner.addCleanupFunction() if any standard cleanup logic is required. 

		def createConfigFile(self, port, configfile='myserverconfig.json'):
			"""
			Create a configuration file for this server using the specified port. 
			
			:param int port: The port number. 
			:param str configfile: The output file. 
			:return str: The path to the created config file. 
			"""
			
			self.owner.write_text(configfile, 
				json.dumps({
				'port':port, 
				'myServerConfigProperty': self.owner.project.getProperty("MyServerHelper.myServerConfigProperty", 12345),
				}), encoding='utf-8')
			return os.path.join(self.owner.output, configfile)

		# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
		# That approach allows you to later customize the logic by changing just one single place, and also to omit 
		# it for specific tests where it is not wanted. 
		def checkLog(self, logfile='my_server.out', ignores=[]):
			"""
			Asserts that the specified log file does not contain any errors. 
			"""
			self.owner.assertGrep(logfile, r'( ERROR | FATAL |Traceback [(]most recent call last[)]).*', contains=False, 
				ignores=ignores or ['ERROR .*Expected error'], mappers=[pysys.mappers.JoinLines.PythonTraceback()])

		def startServer(self, name="my_server", arguments=[], waitForServerUp=True, **kwargs):
			"""
			Start this server as a background process on a dynamically assigned free port, and wait for it to come up. 
			
			:param str name: A logical name for this server (in case a single test starts several of them). 
				Used to define the default stdouterr and displayName
			:param list[str] arguments: Arguments to pass to the server. 
			:param bool waitForServerUp: Wait until the server is ready to handle requests (ignored if background is set to False). 
			:param kwargs: Additional keyword arguments are passed through to `pysys.basetest.BaseTest.startProcess()`. 
			"""
			# As this is a server, start in the background by default, but allow user to override by specifying background=False
			kwargs.setdefault('background', True)

			# Use allocateUniqueStdOutErr to make sure if we have multiple instances in this test they don't use the same stdout/err files
			kwargs.setdefault('stdouterr', self.owner.allocateUniqueStdOutErr(name))
			
			if '--port' not in arguments and '--configfile' not in arguments:
				serverPort = self.owner.getNextAvailableTCPPort()
				arguments = arguments+['--port', str(serverPort)]
			else:
				serverPort = None
			kwargs.setdefault('displayName', f'{name}<port {serverPort or "?"}>')
			
			# Could optionally call addCleanupFunction to send a graceful shutdown request to the server port, rather than 
			# relying on hard kill PySys does by default during cleanup
			
			# Use startPython rather than startProcess here so we can get Python code coverage
			process = self.owner.startPython(
				arguments=[self.owner.project.appHome+'/my_server.py']+arguments,
				info={'port':serverPort},
				
				# NB: always pass through **kwargs when defining a startProcess wrapper
				**kwargs)
			if waitForServerUp and kwargs['background']:
				self.owner.waitForGrep(process.stdout, 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], process=process)
			
			# Register a cleanup function that will attempt to request a clean shutdown, since otherwise code coverage isn't written
			if serverPort:
				self.owner.addCleanupFunction(lambda: self.shutdownServer(process), ignoreErrors=False)

			process.info = {'port': serverPort}
			return process
		
		def shutdownServer(self, server, timeout=pysys.constants.TIMEOUTS['WaitForProcessStop'], **kwargs):
			"""
			Cleanly shutdown the specified server. 
			
			Raises an error if the process is not running or if the port of this server is not known. 
			"""
			if not server.running(): return
			urllib.request.urlopen(f'http://127.0.0.1:{server.info["port"]}/shutdown').close()
			server.wait(timeout, **kwargs)
