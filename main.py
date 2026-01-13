"""Entrypoint that starts the Flask runtime and the GUI.

Run this file directly (recommended):

	python main.py

"""

import multiprocessing as mp
import time
import sys

from Backend import runner




def main():
	runtime_proc = None
	try:
		# Use runner to start runtime in a separate process
		runner.run('Backend.runtime', name='runtime', mode='process')
		print('[main] Started runtime via runner')

		# Run the GUI in the main thread using runner (mode='main').
		# This call blocks until the GUI exits.
		try:
			runner.run('Backend.CozmoUI', name='gui', mode='main')
		except Exception as e:
			print('[main] GUI raised an exception:', e)
			raise
		else:
			print('[main] GUI exited normally')

	except KeyboardInterrupt:
		print('\n[main] KeyboardInterrupt received, shutting down...')
	finally:
		# Ensure runner kills any managed children
		try:
			runner.kill_all()
		except Exception:
			pass
		# Give OS a moment to terminate processes and flush logs
		try:
			import time as _time
			_time.sleep(0.5)
		except Exception:
			pass


if __name__ == '__main__':
	try:
		mp.freeze_support()
	except Exception:
		pass

	main()
