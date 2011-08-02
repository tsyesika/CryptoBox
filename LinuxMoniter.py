import pynotify, pyinotify, sys

mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE

class EventHandler(pyinotify.ProcessEvent):
	def process_IN_CREATE(self, event):
		global mfiles
		mfiles["C"].append(event.pathname)
	def process_IN_DELETE(self, event):
		global mfiles
		mfiles["D"].append(event.pathname)
	def process_IN_MODIFY(self, event):
		global mfiles
		mfiles["M"].append(event.pathname)

def ShowIt(x):
	n = pynotify.Notification("CryptoBox", x, "dialogue-warning")
	n.show()

if __name__ == "__main__":
	mfiles = {"C":[], "D":[], "M":[]}
	wm = pyinotify.WatchManager()
	handler = EventHandler()
	notifier = pyinotify.Notifier(wm, handler)
	wdd = wm.add_watch(sys.argv[1], mask, rec=True)
	while notifier.check_events():
		notifier.read_events()
		notifier.process_events()
		# Check mfiles as it should be populated now.
		if mfiles["C"]:
			ShowIt("Created: %s" % ",".join(mfiles["C"]))
			# Do stuff with them/it?
			mfiles["C"] = []
		elif mfiles["D"]:
			ShowIt("Deleted: %s" % ",".join(mfiles["D"]))
			# Do stuff with them/it?
			mfiles["D"] = []
		elif mfiles["M"]:
			ShowIt("Modified: %s" % ",".join(mfiles["M"]))
			# Do stuff with them/it?
			mfiles["M"] = []
		
