from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado
from pubnub.pnconfiguration import PNReconnectionPolicy
from datetime import datetime as dt

config = PNConfiguration()
config.subscribe_key = 'sub-c-52a9ab50-291b-11e5-baaa-0619f8945a4f'
config.reconnect_policy = PNReconnectionPolicy.LINEAR
pubnub = PubNubTornado(config)

from tornado import gen

@gen.coroutine
def main(channels):
    class BitflyerSubscriberCallback(SubscribeCallback):
        
        def __init__(self):
            self.first = True
            self.timestamp = 0.0
            self.sellsum = 0.0
            self.buysum = 0.0
            self.maxsellsum = 0.0
            self.maxbuysum = 0.0

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
                # print('sell')
                # print(self.sellsum)
                # print('buy')
                # print(self.buysum)
                # print('-------------------')
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