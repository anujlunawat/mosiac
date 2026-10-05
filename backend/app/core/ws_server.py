# from pycrdt_websocket import WebsocketServer
from pycrdt.websocket import WebsocketServer
from app.logging.log import logger

"""
single websocket server imported everywhere
args for WebsockerServer():
    - rooms_ready: controls whether the server starts its room management service initialized
    - auto_clean_rooms: determines whether empty rooms are automatically removed.
    - exception_handler: a custom callback for handling exceptions raised inside the server.
    - log: you can provide your own python logging.logger
"""
websocket_server = WebsocketServer(auto_clean_rooms=False, log=logger)
