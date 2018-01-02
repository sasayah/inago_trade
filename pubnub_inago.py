from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado
from pubnub.pnconfiguration import PNReconnectionPolicy
from datetime import datetime as dt
import bitmex_basic
import os

config = PNConfiguration()
config.subscribe_key = 'sub-c-52a9ab50-291b-11e5-baaa-0619f8945a4f'
config.reconnect_policy = PNReconnectionPolicy.LINEAR
pubnub = PubNubTornado(config)

from tornado import gen

@gen.coroutine
def main(channels):
    
    class board_trade():

        def __init__(self,base_uri, symbol):
            self.symbol = symbol
            self.base_uri = base_uri
            self.bitmex = bitmex_basic.BitMEX(symbol=self.symbol, apiKey=os.environ["API_KEY"], apiSecret=os.environ["API_SECRET"], base_uri=self.base_uri)
            self.market_boards = self.bitmex.market_depth()

        def current_price(self):
            current_bitmex = bitmex_basic.BitMEX(symbol=self.symbol, apiKey=os.environ["API_KEY"], apiSecret=os.environ["API_SECRET"], base_uri=self.base_uri)
            current_market_boards = current_bitmex.market_depth()
            bid = current_market_boards[0]['bidPrice']
            ask = current_market_boards[0]['askPrice']
            return {'bid': bid,'ask': ask}
        
                #仕様は未定
        def decide_volume(self):
            volume = 0
            volume =  self.bitmex.wallet() * self.current_price()['bid']
            print(volume)
            return int(volume)




    class BitflyerSubscriberCallback(SubscribeCallback):
        
        def __init__(self):
            self.first = True
            self.timestamp = 0.0
            self.sellsum = 0.0
            self.buysum = 0.0
            self.maxsellsum = 0.0
            self.maxbuysum = 0.0
            self.ontrade = False
            self.board_trade = board_trade(symbol='XBTUSD', base_uri='https://www.bitmex.com/api/v1/')
            self.position = None

        def presence(self, pubnub, presence):
            pass  # handle incoming presence data

        def status(self, pubnub, status):
            if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                pass  # This event happens when radio / connectivity is lost

            elif status.category == PNStatusCategory.PNConnectedCategory:
                # Connect event. You can do stuff like publish, and know you'll get it.
                # Or just use the connected event to confirm you are subscribed for
                # UI / internal notifications, etc
                pass
            elif status.category == PNStatusCategory.PNReconnectedCategory:
                pass
                # Happens as part of our regular operation. This event happens when
                # radio / connectivity is lost, then regained.
            elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
                pass
                # Handle message decryption error. Probably client configured to
                # encrypt messages and on live data feed it received plain text.

        def message(self, pubnub, message):
            # Handle new message stored in message.message
            # メインの処理はここで書きます
            # 登録したチャンネルからメッセージ(価格の変化など)がくるたび、この関数が呼ばれます
            # bestbid = message.message['best_bid']
            # bestask = message.message['best_ask']
            # tstr = message.message['timestamp']
            # tstr = tstr.replace('T', ' ')
            # tstr = tstr.replace('Z', '')
            # tstr = tstr[:-1]
            # #print('bid_diff')
            # bid_diff = bestbid - self.preb_bestbid
            # if bid_diff != 0.0:
            #     print('bestbid')
            #     print(bestbid)
            #     print('bid_diff')
            #     print(bid_diff)
            # self.preb_bestbid = bestbid
            # tdatetime = dt.strptime(tstr, '%Y-%m-%d %H:%M:%S.%f')
            #print(tdatetime)

            #print("%s : %s" % (message.channel, message.message))
            tstr = message.message[0]['exec_date']
            tstr = tstr.replace('T', ' ')
            tstr = tstr.replace('Z', '')
            tstr = tstr[:-1]
            timestamp = dt.strptime(tstr, '%Y-%m-%d %H:%M:%S.%f')
            if(self.first):
                self.timestamp = timestamp
                self.first = False
            #print((timestamp - self.timestamp).__class__.__name__)
            if(timestamp - self.timestamp < dt.strptime('2017-12-05 12:58:00.500', '%Y-%m-%d %H:%M:%S.%f') - dt.strptime('2017-12-05 12:58:00.000', '%Y-%m-%d %H:%M:%S.%f')):
                if(message.message[0]['side'] == 'SELL'):
                    self.sellsum += message.message[0]['size']
                elif(message.message[0]['side'] == 'BUY'):
                    self.buysum += message.message[0]['size']
            else:
                self.timestamp = timestamp
                print('sell')
                print(self.sellsum)
                print('buy')
                print(self.buysum)
                print('-------------------')
                if(self.sellsum > self.maxsellsum):
                    print('max sell')
                    print(self.sellsum)
                    self.maxsellsum = self.sellsum
                if(self.buysum > self.maxbuysum):
                    print('max buy')
                    print(self.buysum)
                    self.maxbuysum = self.buysum
                self.sellsum = 0.0
                self.buysum = 0.0
                #ここから取引
            print('diff')
            print(self.buysum - self.sellsum)
            print('ontrade')
            print(self.ontrade)
            print('position')
            print(self.position)

            if(not self.ontrade):
                if(self.buysum - self.sellsum > 5):
                    quantity =  3 * self.board_trade.decide_volume()
                    self.ontrade = True
                    self.board_trade.bitmex.buy(quantity = quantity)
                    self.position = 'buy'


                if(self.sellsum - self.buysum > 5):
                    quantity =  3 * self.board_trade.decide_volume()
                    self.ontrade = True
                    self.board_trade.bitmex.sell(quantity = quantity)
                    self.position = 'sell'


            if(self.ontrade):
                if(self.buysum - self.sellsum > 1 and self.position == 'sell'):
                    self.ontrade = False
                    self.board_trade.bitmex.closeAllPosition()
                    self.position = None

                if(self.sellsum - self.buysum > 1 and self.position == 'buy'):
                    self.ontrade = False
                    self.board_trade.bitmex.closeAllPosition()
                    self.position = None











    listener = BitflyerSubscriberCallback()
    pubnub.add_listener(listener)
    pubnub.subscribe().channels(channels).execute()

if __name__ == '__main__':
    channels = [
        #'lightning_ticker_BTC_JPY',
        #'lightning_ticker_FX_BTC_JPY',
        #'lightning_ticker_ETH_BTC',
        'lightning_executions_FX_BTC_JPY'
    ]
    main(channels)
    pubnub.start()