from machine import Pin, RTC
import network
import esp32
import ntptime
import utime
import math

import esp
esp.osdebug(None)

import gc
gc.collect()

try:
  import usocket as socket
except:
  import socket
  
try:
    import ustruct as struct
except:
    import struct



# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "pool.ntp.org"
t_ini_1 = 0
t_ini_2 = 0
t_end_1 = 0
t_end_2 = 0




def save_config():
  try:
    f = open('config.txt','w')
    if t_ini_1<10:
      f.write("0"+str(t_ini_1)+"\n")
    else:
      f.write(str(t_ini_1)+"\n")

    if t_end_1<10:
      f.write("0"+str(t_end_1)+"\n")
    else:
      f.write(str(t_end_1)+"\n")

    if t_ini_2<10:
      f.write("0"+str(t_ini_2)+"\n")
    else:
      f.write(str(t_ini_2)+"\n")
    
    if t_end_2<10:
      f.write("0"+str(t_end_2)+"\n")
    else:           
      f.write(str(t_end_2)+"\n")
    
    f.close()
  except:
    print("Error")

def load_config():
  try:
    f = open('config.txt','r')
    content = f.readlines()
    f.close()
    t_ini_1 = int(content[0][0:2])
    t_end_1 = int(content[1][0:2])
    t_ini_2 = int(content[2][0:2])
    t_end_2 = int(content[3][0:2])
  except:
    print("Error")
    t_ini_1 = 0
    t_ini_2 = 0
    t_end_1 = 0
    t_end_2 = 0 
  return t_ini_1,t_end_1,t_ini_2,t_end_2

def relay_on():
  relay = Pin(12, Pin.OUT)
  global estado

  relay.value(1)
  estado = 'Encendido'
  print("prendiendo relay")

def relay_off():
  relay = Pin(12, Pin.OUT)
  global estado

  relay.value(0)
  estado = 'Apagado'
  print("apagando relay")

def reset_schedule():
  t_ini_1 = 0
  t_ini_2 = 0
  t_end_1 = 0
  t_end_2 = 0  
  save_config()

def time():
  NTP_QUERY = bytearray(48)
  NTP_QUERY[0] = 0x1B
  addr = socket.getaddrinfo(host, 123)[0][-1]
  s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    s2.settimeout(100)
    res = s2.sendto(NTP_QUERY, addr)
    msg = s2.recv(48)
  finally:
    s2.close()
  val = struct.unpack("!I", msg[40:44])[0]
  return val - NTP_DELTA


def schedule(year,month,day,hour,second,estado,t_ini_1,t_end_1,t_ini_2,t_end_2):  
  if t_ini_2>0: #Si tengo dos agendas
    if t_ini_1>0:
      if estado == 'Apagado' and t_ini_1<=hour and t_end_1>hour:
        relay_on()
    if t_end_1>0:
      if estado == 'Encendido' and t_end_1<=hour and hour < t_ini_2:
        relay_off()
    if estado == 'Apagado' and t_ini_2<=hour and t_end_2>hour:
      relay_on()
    if t_end_2>0:
      if estado == 'Encendido' and t_end_2<=hour:
        relay_off()
  else: #Si tengo solo una agenda
    if t_ini_1>0:
      if estado == 'Apagado' and t_ini_1<=hour and t_end_1>=hour:
        relay_on()
    if t_end_1>0:
      if estado == 'Encendido' and t_end_1<=hour:
        relay_off()     

def web_page2(year,month,day,hour,minute,second,estado,message):
  time_string= str(day)+'-'+ str(month)+'-'+str(year)+ "-" +str(hour)+":"+str(minute)+":"+str(second)
  if estado == "Encendido":
    relay_state = ''
  else:
    relay_state = 'checked'
  html = """<html>
   <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
         body{font-family:Arial; text-align: center; margin: 0px auto; padding-top:30px;}
         .switch{position:relative;display:inline-block;width:120px;height:68px}.switch input{display:none}
         .slider{position:absolute;top:0;left:0;right:0;bottom:0;background-color:#ccc;border-radius:34px}
         .slider:before{position:absolute;content:"";height:52px;width:52px;left:8px;bottom:8px;background-color:#fff;-webkit-transition:.4s;transition:.4s;border-radius:68px}
         input:checked+.slider{background-color:#2196F3}
         input:checked+.slider:before{-webkit-transform:translateX(52px);-ms-transform:translateX(52px);transform:translateX(52px)}
      </style>
      <script>function toggleCheckbox(element) { var xhr = new XMLHttpRequest(); if(element.checked){ xhr.open("GET", "/?relay=on", true); }
         else { xhr.open("GET", "/?relay=off", true); } xhr.send(); }
      </script> 
   </head>
   <body>
      <h1> Bomba agua piscina </h1>
      <h4> Fecha: %s</h4>
      <h2> Estado: %s</h2>
      <h3> Comando manual </h3>
      <form NAME="myform4" ACTION = "GET">
        <button name="manualON" type="submit" value="">Encender</button>
      </form>
      <form NAME="myform5" ACTION = "GET">
        <button name="manualOFF" type="submit" value="">Apagar</button>
      </form>
      </span></label>
      <h3> Temporizador 1</h3>
      <form NAME="myform" ACTION = "GET">
         <label for="fname">Hora inicio (0 a 23)</label><br>
         <input type="text" id="time_ini" name="t_ini_1" value=""><br>
         <label for="lname">Hora fin (0 a 23):</label><br>
         <input type="text" id="time_end" name="t_end_1" value=""><br><br>
         <input type="submit" value="Agendar">
      </form>
      <h3> Temporizador 2</h3>
      <form NAME="myform2" ACTION = "GET">
         <label for="fname">Hora inicio (0 a 23)</label><br>
         <input type="text" id="time_ini" name="t_ini_2" value=""><br>
         <label for="lname">Hora fin (0 a 23):</label><br>
         <input type="text" id="time_end" name="t_end_2" value=""><br><br>
         <input type="submit" value="Agendar">
      </form>
      <h2> Agenda 1 </h2>
      <h4> Inicio: %s hs, Fin: %s hs </h4>
      <h2> Agenda 2 </h2>
      <h4> Inicio: %s hs, Fin: %s hs </h4>
      <form NAME="myform3" ACTION = "GET">
        <button name="resetear" type="submit" value="fav_HTML">Resetear agenda</button>
      </form>
      <h4> %s </h4>
   </body>
</html>""" % (time_string,estado,t_ini_1,t_end_1,t_ini_2,t_end_2,message)
  return html

message = ""
estado = 'Apagado'

relay = Pin(12, Pin.OUT)
relay_off()

rtc = RTC()
t = time()
tm = utime.localtime(t)
rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))



t_ini_1,t_end_1,t_ini_2,t_end_2 = load_config()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5) # era 5

while True:
  addr = 'None'
  t_ini_1,t_end_1,t_ini_2,t_end_2 = load_config()
  year,month,day,_,hour,minute,second,_ = rtc.datetime()
  if hour >= 3:
    hour = hour - 3
  else:
    hour = hour + 24 - 3
  if minute==0:
    t = time()
    tm = utime.localtime(t)
    rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
  schedule(year,month,day,hour,second,estado,t_ini_1,t_end_1,t_ini_2,t_end_2)
  if gc.mem_free() < 102000:
    gc.collect()
  try:
    s.settimeout(5.0)
    conn, addr = s.accept()
    if addr!="None":
      print('Got a connection from %s' % str(addr))
      conn.settimeout(10.0)
      request = conn.recv(1024)
      request = str(request)
      print('Content = %s' % request)
      reset_stamp = request.find('resetear')
      relay_on_stamp = request.find('/?relay=on')
      relay_off_stamp = request.find('/?relay=off')
      t_ini_1_stamp = request.find('t_ini_1=')
      t_end_1_stamp = request.find('t_end_1=')
      t_ini_2_stamp = request.find('t_ini_2=')
      t_end_2_stamp = request.find('t_end_2=')
      if request.find('manualON')>0:
        relay_on()
      if request.find('manualOFF')>0:
        relay_off()
      if reset_stamp>1:
        t_ini_1 = 0
        t_ini_2 = 0
        t_end_1 = 0
        t_end_2 = 0
        save_config()
      if t_ini_1_stamp>1:
        t_ini_1 = int(request[t_ini_1_stamp+8:t_ini_1_stamp+10])
        save_config()
      if t_end_1_stamp>1:
        t_end_1 = int(request[t_end_1_stamp+8:t_end_1_stamp+10])
        save_config()
      if t_ini_2_stamp>1:
        t_ini_2 = int(request[t_ini_2_stamp+8:t_ini_2_stamp+10])
        save_config()
      if t_end_2_stamp>1:
        t_end_2 = int(request[t_end_2_stamp+8:t_end_2_stamp+10])
        save_config()
      if relay_on_stamp == 6:
        relay_on()
      if relay_off_stamp == 6:
        relay_off()
      response = web_page2(year,month,day,hour,minute,second,estado,message)
      conn.send('HTTP/1.1 200 OK\n')
      conn.send('Content-Type: text/html\n')
      conn.send('Connection: close\n\n')
      conn.sendall(response)
      conn.close()
  except OSError as e:
    if addr!="None":
      conn.close()
      print('Connection closed')
