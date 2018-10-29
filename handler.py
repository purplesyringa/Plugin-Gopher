from Site import SiteManager

def handler(path, ip, port):
	path = path.strip("/")

	# Parse path.
	# Defaults:
	type = "1"
	search = ""
	if "/" in path:
		# We have type and path
		type, path = path.split("/", 1)
	if "/" in path:
		# We also have search string
		path, search = path.split("/", 1)

	if search != "":
		# Search isn't supported
		yield "3", "Search is not supported yet."
		return

	# Handle home page
	if path == "":
		yield "i", "Welcome to ZeroNet Gopher proxy!"
		yield "i", "Site list follows:"
		yield

		for address, site in SiteManager.site_manager.sites.iteritems():
			# Try to get site title
			try:
				content_json = site.content_manager.contents["content.json"]
				title = content_json["title"]
			except:
				# Fallback to address
				title = address

			yield "1", title, address, ip, port