from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
from .models import ChartData
import pyads
import re
import threading
import time

is_recording = False
recording_thread = None
trigger_check_thread = None
dropdown_map = {
    'MAN': 0,
    'AKR': 1,
    'RKR': 2,
    'LRE': 3,
    'KLU': 4,
    'LKU': 5,
    'KRU': 6,
    'KRu': 7,
    'KI': 8,
    }

# Set up ADS connection parameters
PLC_AMS_ID = '192.168.178.137.1.1'  # Replace with your PLC's AMS Net ID
PLC_IP = '192.168.188.21'  # Replace with your PLC's IP address
PLC_PORT = 851  # The default port for ADS communication
plc = pyads.Connection(PLC_AMS_ID, PLC_PORT, PLC_IP)
def test_plc_connection():

    try:
        # Open the connection to the PLC
        plc = pyads.Connection(PLC_AMS_ID, PLC_PORT, PLC_IP)
        plc.open()

        # Check the connection status
        if plc.is_open:
            print("Connection to PLC successful.")
        else:
            print("Failed to connect to PLC.")
        
        # Close the connection
        plc.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_plc_connection()

def clean_string(value):
    # Remove non-printable characters and specific problematic characters like semicolons
    return re.sub(r'[^\x20-\x7E]', '', value).replace(';', '').strip()

def nothalt(request):
    if request.method == 'POST':
        with plc:
            plc.write_by_name('MAIN.irs', 0, pyads.PLCTYPE_INT)
        return JsonResponse({'status': 'Nothalt triggered'})
    return JsonResponse({'status': 'Invalid request'}, status=400)


def home(request):
    return render(request,'desktop/desktop_h.html')

def eingabe(request):

    global dropdown_map

    if request.method == 'POST':
        sollkraft = float(request.POST.get('sollkraft'))
        sollspalt = float(request.POST.get('sollspalt'))
        umschaltwert = int(request.POST.get('umschaltwert'))
        verstaerkungsfaktor = int(request.POST.get('verstaerkungsfaktor'))
        motoren_zustand = request.POST.get('motoren_zustand') == 'on'
        start_stopp = request.POST.get('start_stopp') == 'on'
        prozess_aktiv = request.POST.get('prozess_aktiv') == 'on'
        dropdown1 = request.POST.get('dropdown1')

        irs_value = dropdown_map.get(dropdown1, 0) 

    

        with plc:
            plc.write_by_name('MAIN.Soll_Kraft', sollkraft, pyads.PLCTYPE_REAL)
            plc.write_by_name('MAIN.Soll_Lage', sollspalt, pyads.PLCTYPE_REAL)
            plc.write_by_name('MAIN.Soll_Umschaltung', umschaltwert, pyads.PLCTYPE_INT)
            plc.write_by_name('MAIN.amp_Kraft', verstaerkungsfaktor, pyads.PLCTYPE_INT)
            plc.write_by_name('MAIN.irs', irs_value, pyads.PLCTYPE_INT)
            plc.write_by_name('MAIN.Prozess_aktiv', prozess_aktiv, pyads.PLCTYPE_BOOL)
            if motoren_zustand==True:
                plc.write_by_name('MAIN.M_Pos_Work', True, pyads.PLCTYPE_BOOL)
                plc.write_by_name('MAIN.M_Pos_Home', False, pyads.PLCTYPE_BOOL)
            else:
                plc.write_by_name('MAIN.M_Pos_Work', False, pyads.PLCTYPE_BOOL)
                plc.write_by_name('MAIN.M_Pos_Home', True, pyads.PLCTYPE_BOOL)


            if start_stopp==True:
                plc.write_by_name('MAIN.M_Init', True, pyads.PLCTYPE_BOOL)
                plc.write_by_name('MAIN.M_Start', True, pyads.PLCTYPE_BOOL)
            else:
                plc.write_by_name('MAIN.M_Init', False, pyads.PLCTYPE_BOOL)
                plc.write_by_name('MAIN.M_Start', False, pyads.PLCTYPE_BOOL)
        return redirect('eingabe_url')

    with plc:
        sollkraft = plc.read_by_name('MAIN.Soll_Kraft', pyads.PLCTYPE_REAL)
        sollspalt = plc.read_by_name('MAIN.Soll_Lage', pyads.PLCTYPE_REAL)
        umschaltwert = plc.read_by_name('MAIN.Soll_Umschaltung', pyads.PLCTYPE_INT)
        verstaerkungsfaktor = plc.read_by_name('MAIN.amp_Kraft', pyads.PLCTYPE_INT)
        motoren_zustand = plc.read_by_name('MAIN.M_Pos_Work', pyads.PLCTYPE_BOOL)
        start_stopp = plc.read_by_name('MAIN.M_Init', pyads.PLCTYPE_BOOL)
        irs_value = plc.read_by_name('MAIN.irs', pyads.PLCTYPE_INT)
        prozess_aktiv = plc.read_by_name('MAIN.Prozess_aktiv', pyads.PLCTYPE_BOOL)



    context = {
        'sollkraft': sollkraft,
        'sollspalt': sollspalt,
        'umschaltwert': umschaltwert,
        'verstaerkungsfaktor': verstaerkungsfaktor,
        'motoren_zustand': motoren_zustand,
        'start_stopp': start_stopp,
        'prozess_aktiv':prozess_aktiv,
        'dropdown_map': dropdown_map,
        'irs_value':irs_value,
        
    
    }

    return render(request, 'desktop/Heingabe.html', context)



def start_recording():
    global is_recording, recording_thread

    def record_data():
        while is_recording:
            try:
                with plc:
                    time_value = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    soll_spalt_value = plc.read_by_name('MAIN.Soll_Lage', pyads.PLCTYPE_REAL)
                    sensor1_str = plc.read_by_name('ADWin.rWeg1', pyads.PLCTYPE_REAL)
                 #   sensor2_str = plc.read_by_name('ADWin.rWeg2', pyads.PLCTYPE_REAL)
                    sensor3_str = plc.read_by_name('ADWin.rWeg3', pyads.PLCTYPE_REAL)
                    kraft_sensor1 = plc.read_by_name('ADWin.rKraft1', pyads.PLCTYPE_REAL)
                    kraft_sensor2 = plc.read_by_name('ADWin.rKraft2', pyads.PLCTYPE_REAL)
                    soll_kraft = plc.read_by_name('MAIN.Soll_Kraft', pyads.PLCTYPE_REAL)
                    KI_1 = plc.read_by_name('MAIN.real_aSplit[0]', pyads.PLCTYPE_REAL)
                    KI_2 = plc.read_by_name('MAIN.real_aSplit[1]', pyads.PLCTYPE_REAL)

                data = {
                    'time': time_value,
                    'soll_spalt': soll_spalt_value,
                    'sensor1_str': sensor1_str,
                   # 'sensor2_str': sensor2_str,
                    'sensor3_str': sensor3_str,
                    'kraft_sensor1': kraft_sensor1,
                    'kraft_sensor2': kraft_sensor2,
                    'soll_kraft': soll_kraft,
                    'KI_1': KI_1,
                    'KI_2': KI_2
                }
                ChartData.objects.create(**data)
                time.sleep(1)
            except Exception as e:
                print(f"Error during recording: {e}")

    if not recording_thread or not recording_thread.is_alive():
        is_recording = True
        recording_thread = threading.Thread(target=record_data)
        recording_thread.start()

def stop_recording():
    global is_recording
    is_recording = False

def check_trigger(response):
    global is_recording
    try:
        with plc:
            trigger_value = plc.read_by_name('MAIN.Prozess_aktiv', pyads.PLCTYPE_BOOL)

        if trigger_value and not is_recording:
            ChartData.objects.all().delete()
            start_recording()
        elif not trigger_value and is_recording:
            stop_recording()
    except Exception as e:
        print(f"Error during trigger check: {e}")
    return JsonResponse({'trigger': trigger_value})

def start_trigger_check():
    global trigger_check_thread

    def trigger_check():
        while True:
            check_trigger()
            time.sleep(1)

    if not trigger_check_thread or not trigger_check_thread.is_alive():
        trigger_check_thread = threading.Thread(target=trigger_check)
        trigger_check_thread.daemon = True
        trigger_check_thread.start()

start_trigger_check()

def chart_data(request):
    global is_recording
    try:
        with plc:
            time_value = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            soll_spalt_value = plc.read_by_name('MAIN.Soll_Lage', pyads.PLCTYPE_REAL)
            sensor1_str = plc.read_by_name('ADWin.rWeg1', pyads.PLCTYPE_REAL)
          #  sensor2_str = plc.read_by_name('ADWin.rWeg2', pyads.PLCTYPE_REAL)
            sensor3_str = plc.read_by_name('ADWin.rWeg3', pyads.PLCTYPE_REAL)
            kraft_sensor1 = plc.read_by_name('ADWin.rKraft1', pyads.PLCTYPE_REAL)
            kraft_sensor2 = plc.read_by_name('ADWin.rKraft2', pyads.PLCTYPE_REAL)
            soll_kraft = plc.read_by_name('MAIN.Soll_Kraft', pyads.PLCTYPE_REAL)
            KI_1 = plc.read_by_name('MAIN.real_aSplit[0]', pyads.PLCTYPE_REAL)
            KI_2 = plc.read_by_name('MAIN.real_aSplit[1]', pyads.PLCTYPE_REAL)

        data = {
            'time': time_value,
            'soll_spalt': soll_spalt_value,
            'sensor1_str': sensor1_str,
         #   'sensor2_str': sensor2_str,
            'sensor3_str': sensor3_str,
            'kraft_sensor1': kraft_sensor1,
            'kraft_sensor2': kraft_sensor2,
            'soll_kraft': soll_kraft,
            'KI_1': KI_1,
            'KI_2': KI_2
        }
        if is_recording:
            ChartData.objects.create(**data)

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)}, status=500)

def get_recorded_data(request):
    try:
        data = list(ChartData.objects.all().values())
        return JsonResponse({'recorded_data': data})
    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)}, status=500)

def charts(request):
    return render(request, 'desktop/charts.html')

    
def ausgabe(request):
    global dropdown_map
    reverse_dropdown_map = {v: k for k, v in dropdown_map.items()}

    with plc:
        # Read current values from the PLC
        sensor1_str = clean_string(plc.read_by_name('MAIN.sensor1_str', pyads.PLCTYPE_STRING))
        sensor2_str = clean_string(plc.read_by_name('MAIN.sensor2_str', pyads.PLCTYPE_STRING))
        sensor3_str = clean_string(plc.read_by_name('MAIN.sensor3_str', pyads.PLCTYPE_STRING))
        X1_Kraft_str = clean_string(plc.read_by_name('MAIN.X1_Kraft_str', pyads.PLCTYPE_STRING))
        X2_Kraft_str = clean_string(plc.read_by_name('MAIN.X2_Kraft_str', pyads.PLCTYPE_STRING))
        irs = plc.read_by_name('MAIN.irs', pyads.PLCTYPE_INT)
        amp_Kraft = plc.read_by_name('MAIN.amp_Kraft', pyads.PLCTYPE_INT)
        MC1iActualPosition_Mc1_str = clean_string(plc.read_by_name('MAIN.MC1iActualPosition_Mc1_str', pyads.PLCTYPE_STRING))
        MC2iActualPosition_Mc2_str = clean_string(plc.read_by_name('MAIN.MC2iActualPosition_Mc2_str', pyads.PLCTYPE_STRING))
        Prozess_aktiv = plc.read_by_name('MAIN.Prozess_aktiv', pyads.PLCTYPE_BOOL)

        
    regelungsstrategie = reverse_dropdown_map.get(irs, 'Unknown')



    context = {
        'sensor1_str': sensor1_str,
        'sensor2_str': sensor2_str,
        'sensor3_str': sensor3_str,
        'X1_Kraft_str': X1_Kraft_str,
        'X2_Kraft_str': X2_Kraft_str,
        'irs': regelungsstrategie,
        'amp_Kraft': amp_Kraft,
        'MC1iActualPosition_Mc1_str': MC1iActualPosition_Mc1_str,
        'MC2iActualPosition_Mc2_str': MC2iActualPosition_Mc2_str,
        'Prozess_aktiv': Prozess_aktiv,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(context)

    current_datetime = datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
    context['current_datetime'] = current_datetime

    return render(request, 'desktop/ausgabe.html', context  )

# Create your views here.
