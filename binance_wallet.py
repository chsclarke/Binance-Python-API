"""
Copyright 2018 Chase Clakre chsclarke11@gmail.com
    - this is a program for pulling wallet data from binance and sending an investment report by email
"""
#binance imports
import json
from binance.client import Client

#google imports
import httplib2
import os
import oauth2client
from oauth2client import client, tools
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery

#for file imports from working directory
import json

#API key, secret for 'Floor' api.
api_key = "<xxx KEY xxxx>"
api_secret = "<xxxx SECRET xxxx>"
client = Client(api_key, api_secret)


def get_wallet():
    """returns any coin you own - or a list of dictionaries filled with all non 0 values and time of execution corresponding to 'free', 'locked' dict. key from client.get_account()"""
    
    #get all asset info
    info = client.get_account()
    temp_wallet = []
    wallet = {}
    
    #finding all non 0 values
    for i in info['balances']:
        if i['free'] != '0.00000000' or i['locked'] != '0.00000000':
            temp_wallet.append(i)

    wallet['time'] = info['updateTime']
    wallet['assets'] = temp_wallet

    return wallet



def get_estimated_values(wallet):
    """returns the total estimated value of coin sums in your wallet."""
    #wallet = get_wallet()
    list_of_coins =[]
    prices = client.get_all_tickers()
    ETHUSDT = 0
    sum_usd =[]
    ETH_value = 0
    sum_USDT = 0
    estimated_values = []
    temp_dict = {}
    
    for i in prices: #finding ETHUSDT conversion
        if i['symbol'] == 'ETHUSDT':
            ETHUSDT = float(i['price'])

    for a in wallet['assets']: #finding USDT value of individual sums of coins in wallet
        for b in prices:
            if a['asset']+'ETH' == b['symbol']:
                ETH_value = (float(a['free']) + float (a['locked'])) * float(b['price'])
                sum_USDT = (ETH_value * ETHUSDT)
                temp_dict['asset'] = a['asset']
                temp_dict['quantity'] = str(float(a['free'])+float(a['locked']))
                temp_dict['sum USDT'] = str(sum_USDT)
                estimated_values.append(temp_dict)
                temp_dict = {}
                ETH_value = 0
                sum_USDT = 0

    for c in wallet['assets']: #extra loop to get value USDT
        if c['asset'] == 'USDT':
            temp_dict['asset'] = a['asset']
            temp_dict['quantity'] = str(float(c['free'])+float(c['locked']))
            temp_dict['sum USDT'] = str(float(c['free']) + float(c['locked']))
            estimated_values.append(temp_dict)
            temp_dict = {}
            ETH_value = 0
            sum_USDT = 0

    for d in wallet['assets']: #extra loop to get value ETH
        if d['asset'] == 'ETH':
            temp_dict['asset'] = d['asset']
            temp_dict['quantity'] = str(float(d['free'])+float(d['locked']))
            temp_dict['sum USDT'] = str((float(d['free']) + float(d['locked'])) * ETHUSDT)
            estimated_values.append(temp_dict)
            temp_dict = {}
            ETH_value = 0
            sum_USDT = 0

    return estimated_values


def get_estimated_total_value(wallet_USDT):
    """returns the total sum of investments in your wallet."""
    sum = 0
    
    for i in wallet_USDT: #sums all the usdt values of coins in wallet.
       sum = sum + float(i['sum USDT'])

    return sum



def display_estimated_values(all_estimated_values):
    """takes all_estimated_values() a list of dictionaries and makes it presentable for the email. Does not show values less than 15 dollars USDT"""
    #all_estimated_values = get_estimated_values()
    output_str = ""
    for i in all_estimated_values:
        if float(i['sum USDT']) > 15.00:
            output_str += i['asset'] + ":<p>"
            output_str += "<li>"+"quantity = "+ i['quantity'][:11] +"</li>"
            output_str += "<li>"+"USDT value = $"+ i['sum USDT'][:11] +"</li>"
            output_str += "</p>"
    return output_str


def read_data():
    """reads past trade data from current text file"""
    file1 = open("data/email_data.txt","r+")
    return_file = file1.read()
    return_file = json.loads(return_file)
    file1.close()
    
    return return_file


def write_data(current_data):
    """writes current data to current and history text file."""
    #deleting current file and writing updated info
    file1 = open("data/email_data.txt","w") #write (w) mode so file WILL overwrite
    L = [json.dumps(current_data)]
    file1.writelines(L)
    file1.close()
    #writing to the history file
    file2 = open("data/email_data_history.txt","a") #append (a) mode so file will NOT overwrite
    L = json.dumps(current_data)
    file2.write(L)
    file2.close()


# ------- end of binance functions ------- #
wallet_print = get_wallet() #wallet to be printed to text file
all_estimated_values = get_estimated_values(wallet_print) #esitmated values to be printed to text file
wallet_sum = get_estimated_total_value(all_estimated_values)

# ------- beginnning of the Google Gmail API code ------- #

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'binace_wallet'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def SendMessage(sender, to, subject, msgHtml, msgPlain):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message1 = CreateMessage(sender, to, subject, msgHtml, msgPlain)
    SendMessageInternal(service, "me", message1)

def SendMessageInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def CreateMessage(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    raw = base64.urlsafe_b64encode(msg.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}
    return body

def main():
    print_list = [] #building list so timestamp will be in print
    print_list.append(all_estimated_values)
    print_list.append(wallet_print)
    difference = float(wallet_sum) - float(get_estimated_total_value(read_data()[0]))
    write_data(print_list) #writing data to text files
    #defining the color for gain or loss on the email
    if difference >= 0:
        gl_color = "green"
    else:
        gl_color = "red"


    to = "<xxxx ACCOUNT HOLDERS EMAIL xxxx>"
    sender = "<xxxx SENDERS EMAIL xxxx>"
    subject = "Daily Crypto Digest"
    

    #email_message = "Morning,<br/> Your investments are worth: ${} USDT<br/><br/>You are currently invested in:<br/><br/> {}<br/><br/> Your net since last week is approximatelly: ${} USDT."
    YOUR_INITIAL_DEPOSIT = 0000.00

    email_message = """
    <html>
      <head>
        <style>
          .red {
            color: red;
          }
          .green {
            color: green;
          }
          #body {
            font-size: 14px;
            font-family: Times New Roman;
            font-type: Bold;
          }
          </style>
        </head>
        
        <body>
          <div id='body'>
            <p>
              Morning,
            </p>
        
            <p>
              Your investments are worth:
              <p class='"""+gl_color+"""'>
                $"""+str(wallet_sum)[:11]+""" USDT
              </p=>
            </p>
            
            <p>
              You are currently invested in:<br/>
            </p>
            <p>
              """+display_estimated_values(all_estimated_values)+"""
            </p>
        
            <p>
              Your net since yesterday is approximately:
            <p class='"""+gl_color+"""'>
                $"""+str(difference)[:6]+""" USDT<br/></p=>
            </p>
            <p>
              Accounting for the above gain and your innitial deposit of $4383.00 you have a incured a total profit of $"""+ (str(wallet_sum - YOUR_INITIAL_DEPOSIT)[:11]) +""". This profit reflects a """+str(((wallet_sum - YOUR_INITIAL_DEPOSIT)/YOUR_INITIAL_DEPOSIT)*(100))[:6]+"""% gain.
            </p>
          </div>
        </body>
    </html>
    """

    msgHtml = (email_message)


    msgPlain = "Hi\nPlain Email"
    SendMessage(sender, to, subject, msgHtml, msgPlain)



if __name__ == '__main__':
    main()





