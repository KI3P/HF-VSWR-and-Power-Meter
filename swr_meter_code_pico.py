import machine
import utime
from machine import ADC
from ssd1306 import SSD1306_I2C

#madori button
#button1 = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)
#Pinacolada Button
#button2 = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN)
#led = machine.Pin(25, machine.Pin.OUT)

# Display configuration
sda=machine.Pin(4)
scl=machine.Pin(5)
i2c=machine.I2C(0,sda=sda, scl=scl, freq=400000)
oled = SSD1306_I2C(128, 32, i2c)

# ADC configuration
# GPIO 26 == ADCf == board pin 31
# GPIO 27 == ADCr == board pin 32
ADCf = ADC(26)
ADCr = ADC(27)
# Attenuation between TX line and detector in dB
ATT_dB = -56
# only calculate SWR if forward power is greater than this
power_threshold_W = 0.5 

oled.text("KO4THB", 30, 0)
oled.text("SWR Meter", 10, 10)
oled.text("100 W max",10,20)
oled.show()

utime.sleep(5)

def read_and_average(ADCf,ADCr,N=100):
    # 100 iterations of this function takes 3.5 ms
    smf = 0
    smr = 0
    pkf = 0
    for k in range(N):
        f = ADCf.read_u16()
        smr += (ADCr.read_u16())**2
        smf += f**2
        if f > pkf:
            pkf = f
    return (smf/N)**(0.5) * 3.3 / 65536, (smr/N)**(0.5) * 3.3 / 65536, pkf* 3.3 / 65536

def measure_swr():
    Vf_RMS,Vr_RMS,Vf_peak = read_and_average(ADCf,ADCr,10000)

    Pf_RMS_W = 10**( Vf_RMS/0.24 -3 -(95+ATT_dB)/10)
    Pf_peak_W = 10**( Vf_peak/0.24 -3 -(95+ATT_dB)/10)
    
    A = 10**((Vr_RMS - Vf_RMS)/0.48)
    if Pf_peak_W > power_threshold_W:
        SWR = (1+A)/(1-A)
        SWR_inac = 0.0
    else:
        SWR = 0.0
        SWR_inac = (1+A)/(1-A)
        
    return Pf_RMS_W, Pf_peak_W , SWR, SWR_inac, Vf_RMS, Vr_RMS

while True:
    Pf_RMS,Pf_peak,swr,swr_inac, Vf, Vr = measure_swr()
    machine.Pin(25, machine.Pin.OUT).value(1)
    utime.sleep(0.05)
    machine.Pin(25, machine.Pin.OUT).value(0)
    
    oled.fill(0)
    oled.text("PR=%2.1f"%Pf_RMS, 0, 0)
    oled.text("PP=%2.1f"%Pf_peak, 64, 0)
    oled.text("SWR=%3.2f"%swr, 0, 10)
    oled.text(" S*=%3.2f"%swr_inac, 64, 10)
    oled.text("Vf=%4.3f"%Vf, 0, 20)
    oled.text("Vr=%4.3f"%Vr, 64, 20)
    oled.show()
    #utime.sleep(0.5)
