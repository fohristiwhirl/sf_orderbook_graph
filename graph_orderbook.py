import json, os, queue, sys, threading, time
import pygame; from pygame.locals import *

import stockfighter_basic as sf


# sf.set_web_url(web = "http://127.0.0.1:8000/ob/api/")
# sf.set_web_url(web = "http://medecau.servebeer.com:8000/ob/api/")
# sf.set_web_url(web = "https://api.stockfighter.io/ob/api/")
sf.set_web_url(web = "http://core.mumbaitex.com/ob/api/")

INSTRUCTIONS = '''Realtime Stockfighter book grapher
by Fohristiwhirl a.k.a. Amtiskaw

Instructions:
Change zoom with mouse wheel.
Drag graph by holding the mouse button.

Green  : bid
Red    : ask
'''

# sf.use_localhost()

class Application ():
	def __init__(self, venue, symbol, width, height, y_scale):
		
		self.width = width
		self.height = height
		
		self.y_scale = y_scale
		self.mid_x = None
		
		self.cumulative_draw = True
		
		pygame.init()
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.fpsClock = pygame.time.Clock()
		
		self.data = Data(venue, symbol)
		self.devices = Devices()
	
	def cls(self):
		self.screen.fill(pygame.Color(0,0,0))
	
	def flip(self):
		pygame.display.update()
	
	def handle_inputs(self):

		if self.devices.x_movement:
			self.set_caption()

		if self.devices.button:
			if self.mid_x is not None:
				self.mid_x -= self.devices.x_movement
				self.set_caption()
			
		if self.devices.mwheel_rolled_up:
			self.y_scale *= 1.2
			self.set_caption()

		if self.devices.mwheel_rolled_down:
			self.y_scale /= 1.2
			self.set_caption()
	
	def set_caption(self):
		pygame.display.set_caption("{} {}  (mouse: {})".format(
											self.data.venue,
											self.data.symbol,
											(self.devices.mousex + self.mid_x - self.width // 2) if self.mid_x else None
										)
									)
	
	def draw_data(self):
		self.cls()
		
		
		
		
		midprice = self.mid_x
		if not midprice:
			return

			

		if self.cumulative_draw:
			lastprice = None
			cumulative_bid_qty = 0
			for price, qty in sorted(self.data.mergedbids.items(), reverse = True):
				x_offset = price - midprice
				if lastprice:
					lastprice_x_offset = lastprice - midprice
					x1 = self.width // 2 + lastprice_x_offset
					x2 = self.width // 2 + x_offset
					pygame.draw.line(self.screen, (0,255,0), (x1, (self.height // 2) - cumulative_bid_qty * self.y_scale), (x2, (self.height // 2) - cumulative_bid_qty * self.y_scale))
				lastprice = price
				cumulative_bid_qty += qty
			if lastprice:
				lastprice_x_offset = lastprice - midprice
				x1 = self.width // 2 + lastprice_x_offset
				x2 = 0
				pygame.draw.line(self.screen, (0,255,0), (x1, (self.height // 2) - cumulative_bid_qty * self.y_scale), (x2, (self.height // 2) - cumulative_bid_qty * self.y_scale))
		
		lastprice = None
		for price, qty in self.data.mergedbids.items():
			x_offset = price - midprice
			x = self.width // 2 + x_offset
			pygame.draw.line(self.screen, (0,255,0), (x, self.height // 2 + 10), (x, self.height // 2 + 10 + qty * self.y_scale))
		
		
		
		if self.cumulative_draw:
			lastprice = None
			cumulative_ask_qty = 0
			for price, qty in sorted(self.data.mergedasks.items(), reverse = False):
				x_offset = price - midprice
				if lastprice:
					lastprice_x_offset = lastprice - midprice
					x1 = self.width // 2 + lastprice_x_offset
					x2 = self.width // 2 + x_offset
					pygame.draw.line(self.screen, (255,0,0), (x1, (self.height // 2) - cumulative_ask_qty * self.y_scale), (x2, (self.height // 2) - cumulative_ask_qty * self.y_scale))
				lastprice = price
				cumulative_ask_qty += qty
			if lastprice:
				lastprice_x_offset = lastprice - midprice
				x1 = self.width // 2 + lastprice_x_offset
				x2 = self.width
				pygame.draw.line(self.screen, (255,0,0), (x1, (self.height // 2) - cumulative_ask_qty * self.y_scale), (x2, (self.height // 2) - cumulative_ask_qty * self.y_scale))
		
		lastprice = None
		for price, qty in self.data.mergedasks.items():
			x_offset = price - midprice
			x = self.width // 2 + x_offset
			pygame.draw.line(self.screen, (255,0,0), (x, self.height // 2 + 10), (x, self.height // 2 + 10 + qty * self.y_scale))
	
	
	
	def run(self):
		self.set_caption()
		while 1:
			self.devices.update_state()
			self.handle_inputs()
			
			self.data.update()
			if self.mid_x is None:
				if self.data.midpoint:
					self.mid_x = self.data.midpoint
					self.set_caption()
			
			self.cls()
			self.draw_data()
			self.flip()
			
			self.fpsClock.tick(60)


class Devices ():
	def __init__(self):
		# Long lasting traits:
		self.mousex = 0
		self.mousey = 0
		self.button = False
		self.keysdown = set()
		# Single tick traits:
		self.x_movement = 0
		self.y_movement = 0
		self.mwheel_rolled_down = False
		self.mwheel_rolled_up = False
	
	def update_state(self):
		self.x_movement = 0
		self.y_movement = 0
		self.mwheel_rolled_down = False
		self.mwheel_rolled_up = False
	
		for event in pygame.event.get():
		
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			
			elif event.type == MOUSEMOTION:
				oldx, oldy = self.mousex, self.mousey
				self.mousex, self.mousey = event.pos
				self.x_movement += self.mousex - oldx
				self.y_movement += self.mousey - oldy
			
			elif event.type == MOUSEBUTTONDOWN:
				if event.button == 1:													# Left-click
					self.button = True
				elif event.button == 4:													# Scroll wheel up
					self.mwheel_rolled_up = True
				elif event.button == 5:													# Scroll wheel down
					self.mwheel_rolled_down = True
	
			elif event.type == MOUSEBUTTONUP:
				if event.button == 1:
					self.button = False
	
			elif event.type == KEYDOWN:
				k = event.key
				self.keysdown.add(k)
			
			elif event.type == KEYUP:
				k = event.key
				self.keysdown.discard(k)


class Data ():
	def __init__(self, venue, symbol):
		self.venue = venue
		self.symbol = symbol
		self.mergedbids = dict()
		self.mergedasks = dict()
		self.midpoint = None
		self.book_queue = queue.Queue()
		
		self.start_ticker()
	
	def start_ticker(self):
		newthread = threading.Thread(target = sf.orderbook_pseudoticker, daemon = True, kwargs = {
										"threads"		: 5,
										"venue"			: self.venue,
										"symbol"		: self.symbol,
										"output_queue"	: self.book_queue}
									)
		newthread.start()
	
	def update(self):
		
		book_found = False
		
		while 1:
			try:
				bk = self.book_queue.get(block = False)
				book_found = True
			except queue.Empty:
				break
			
		if not book_found:
			return
		
		self.mergedbids.clear()
		self.mergedasks.clear()
		
		bids = bk["bids"]
		asks = bk["asks"]
		
		if bids:
			for bid in bids:
				price = bid["price"]
				qty = bid["qty"]
				if price in self.mergedbids:
					self.mergedbids[price] += qty
				else:
					self.mergedbids[price] = qty
		
		if asks:
			for ask in asks:
				price = ask["price"]
				qty = ask["qty"]
				if price in self.mergedasks:
					self.mergedasks[price] += qty
				else:
					self.mergedasks[price] = qty
		
		if self.mergedbids and self.mergedasks:
			best_bid = max(self.mergedbids.keys())
			best_ask = min(self.mergedasks.keys())
		
			self.midpoint = (best_bid + best_ask) // 2
		elif self.mergedbids:
			self.midpoint = max(self.mergedbids.keys())
		elif self.mergedasks:
			self.midpoint = min(self.mergedasks.keys())
		else:
			self.midpoint = None


def main(venue, symbol):
	app = Application(venue, symbol, width = 1800, height = 600, y_scale = 1)
	app.run()
	
if __name__ == "__main__":
	print(INSTRUCTIONS)
	venue = input("Venue? ")
	r = sf.liststocks(venue)
	if r:
		symbol = r["symbols"][0]["symbol"]
		main(venue, symbol)
	else:
		input()
