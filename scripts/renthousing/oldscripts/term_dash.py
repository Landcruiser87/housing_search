import logging
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from time import sleep
from rich.layout import Layout
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import (
	Progress,
	BarColumn,
	SpinnerColumn,
	TextColumn,
	TimeRemainingColumn,
)

class MakeHeader:
	"""Display header with clock."""

	def __rich__(self) -> Panel:
		grid = Table.grid(expand=True)
		grid.add_column(justify="center", ratio=1)
		grid.add_column(justify="right")
		grid.add_row(
			"[b]Super[/b] Duper Application",
			datetime.now().ctime().replace(":", "[blink]:[/]"),
		)
		return Panel(grid, style="red on black")

class MainTableHandler(logging.Handler):
	"""Custom logging handler that saves off every entry of a logger to a temporary
	list.  As the size of the list grows to be more than half the terminal
	height, it will pop off the first item in the list and redraw the
	main_table. 

	Args:
		logging (Handler): modified logging handler. 
	"""	
	def __init__(self, main_table: Table, layout: Layout, log_level: str):
		super().__init__()
		self.main_table = main_table
		self.log_list = []
		self.layout = layout
		self.log_format = "%(asctime)s-(%(funcName)s)-%(lineno)d-%(levelname)s-[%(message)s]"
		self.setLevel(log_level)

	def emit(self, record):
		record.asctime = record.asctime.split(",")[0]
		#msg = self.format(record) #if you want just the message info switch comment lines
		msg = self.log_format % record.__dict__
		tsize = os.get_terminal_size().lines // 2
		if len(self.log_list) > tsize:
			self.log_list.append(msg)
			self.log_list.pop(0)
			self.main_table = redraw_main_table(self.log_list)
			self.layout["termoutput"].update(Panel(self.main_table, border_style="red"))
		else:
			self.main_table.add_row(msg)
			self.log_list.append(msg)


def get_file_handler(log_dir: Path) -> logging:
	"""Assigns format and file handler to the logger object

	Args:
		log_dir (Path): Where you want the log stored. 

	Returns:
		logging: logger object 
	"""	
	log_format = "[%(asctime)s]-[%(funcName)s(%(lineno)d)]-[%(levelname)s]-[%(message)s]"
	log_file = log_dir / "test.log"
	file_handler = logging.FileHandler(log_file)
	file_handler.setFormatter(logging.Formatter(log_format))
	return file_handler


def get_logger(log_dir: Path) -> logging:
	"""Takes in a file path and returns a logger object

	Args:
		log_dir (Path): File Path of where you want the log 

	Returns:
		logging: logger object. 
	"""	
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	logger.addHandler(get_file_handler(log_dir))
	return logger


def make_layout() -> Layout:
	"""Creates the rich Display Layout

	Returns:
		Layout: rich Layout object
	"""	
	layout = Layout(name="root")
	layout.split(
		Layout(name="header", size=3), 
		Layout(name="main")
	)
	layout["main"].split_row(
		Layout(name="leftside"), 
		Layout(name="termoutput")
	)
	layout["leftside"].split_column(
		Layout(name="overall prog", ratio=2), 
		Layout(name="sleep prog")
	)
	return layout

def get_stats() -> Table:
	"""Create rich stats table. 

	Returns:
		Table: rich Table object
	"""	
	rand_arr = np.random.randint(low=2, high=10, size=(10, 6)) + np.random.random((10, 6))
	stats_table = Table(
		expand=True,
		show_header=True,
		header_style="bold",
		title="[magenta][b]Hot Stats![/b]",
		highlight=True,
	)
	stats_table.add_column("Column", justify="right")
	stats_table.add_column("Mean", justify="center")
	stats_table.add_column("Std", justify="center")
	stats_table.add_column("Max", justify="center")
	stats_table.add_column("Min", justify="center")

	for col in range(rand_arr.shape[1]):
		stats_table.add_row(
			f"Col {col}",
			f"{rand_arr[:, col].mean():.2f}",
			f"{rand_arr[:, col].std():.2f}",
			f"{rand_arr[:, col].max():.2f}",
			f"{rand_arr[:, col].min():.2f}",
		)

	return stats_table

def redraw_main_table(temp_list: list) -> Table:
	"""Function that redraws the main table once the log
	entries reach a certain legnth.

	Args:
		temp_list (list): Stores the last 10 log entries

	Returns:
		Table: rich Table object
	"""	
	main_table = Table(
		expand=True,
		show_header=False,
		header_style="bold",
		title="[blue][b]Log Entries[/b]",
		highlight=True,
	)
	main_table.add_column("Log Entries")
	for row in temp_list:
		main_table.add_row(row)

	return main_table

def main():
	console = Console(color_system="truecolor")
	logger = get_logger(Path.cwd())

	main_table = Table(
		expand=True,
		show_header=False,
		header_style="bold",
		title="[blue][b]Log Entries[/b]",
		highlight=True,
	)
	main_table.add_column("Log Output")

	my_progress_bar = Progress(
		SpinnerColumn("balloon2"),
		TextColumn("{task.description}"),
		BarColumn(),
		"time remain:",
		TimeRemainingColumn(),
		TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
	)
	my_counter = range(30)
	my_task = my_progress_bar.add_task("The jobs", total=int(len(my_counter)))

	progress_table = Table.grid(expand=True)
	progress_table.add_row(
		Panel(
			my_progress_bar,
			title="One progress bar to rule them all",
			border_style="green",
			padding=(1, 1),
		)
	)

	stats_table = get_stats()
	layout = make_layout()
	layout["header"].update(MakeHeader())
	layout["progbar"].update(Panel(progress_table, border_style="green"))
	layout["termoutput"].update(Panel(main_table, border_style="blue"))
	layout["stats"].update(Panel(stats_table, border_style="magenta"))

	with Live(layout, refresh_per_second=10, screen=True) as live:
		# Add MainTableHandler to logger
		logger.addHandler(MainTableHandler(main_table, layout, logger.level))
		for count in my_counter:
			sleep(1)
			logger.info(f"I made it to count {count}")
			my_progress_bar.update(my_task, completed=count)

			if count % 5 == 0:
				logger.warning(f"Gettin some STATS")
				stats_table = get_stats()	
				layout["stats"].update(Panel(stats_table, border_style="magenta"))
				logger.critical("Stranger Danger")
			live.refresh()

	logger.info("Done logging.")

if __name__ == "__main__":
	main()
