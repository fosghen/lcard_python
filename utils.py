import ctypes
from ctypes import cdll
from numpy import zeros
from math import ceil

import errors 
import structures


# Подгрузка динамических библиотек для работы 
x502 = cdll.LoadLibrary('x502api.dll')
e502 = cdll.LoadLibrary('e502api.dll')
l502 = cdll.LoadLibrary('l502api.dll')


def get_library_version():
    '''
    Функция выводт на экран текущую версию библиотеки
    '''
    ver = bin(x502.X502_GetLibraryVersion()) # Получем версию библиотеки в виде 32-битного числа
    v_maj = int(ver[:-24], 2) # Мажорная версия
    v_min = int(ver[-24:-16], 2) # Минорная версия
    v_rev = int(ver[-16:-8], 2) # Версия ревизии
    v_num = int(ver[-8:], 2) # Номер сборки
    print(f"Версия библиотеки: {v_maj}.{v_min}.{v_rev}.{v_num}")
    
    

def get_number_available_dev():
    '''
    Функция определяет количество устройств доступных 
    для подключения по USB, выводит информацию об этих
    устройствах
    
    return available_devices[list[t_x502_devrec]]
    список устройств доступных к подключению 
    '''
    p_num_dev_usb = ctypes.pointer(ctypes.c_int32(0)) # Создаём указатель на номер доступных устройств по USB
#     p_num_dev_pci = ctypes.pointer(ctypes.c_int32(0)) # Создаём указатель на номер доступных устройств по PCI
    e502.E502_UsbGetDevRecordsList(None, 0, 0, p_num_dev_usb)
#     l502.L502_GetDevRecordsList(None, 0, 0, p_num_dev_pci)
    
    num_dev = p_num_dev_usb.contents.value # + p_num_dev_pci.contents.value
    print("Количество доступных устройств:", num_dev)
    
    dev_rec = (structures.t_x502_devrec*num_dev)()
    
    e502.E502_UsbGetDevRecordsList(dev_rec, num_dev, 0, p_num_dev_usb)
    
    available_devices = []
    
    for i in range(num_dev):
        if dev_rec[i].sign == int("4C524543", 16):
            print(f"№ {i + 1}, ", end='')
            print(f"устройство {dev_rec[i].devname.decode()}, ", end='')
            print(f"серийный номер {dev_rec[i].serial.decode()}, ", end='')
            if dev_rec[i].iface == 1:
                print("USB")

            if dev_rec[i].iface == 2:
                print("Ethernet")

            if dev_rec[i].iface == 3:
                print("PCI")
                
            available_devices.append(dev_rec[i])
    return available_devices
             

def connect_to_dev(available_devices, num_dev):
    '''
    Создание описателя модуля и подключение к одному 
    из списка доступных к подлючению устройств
    
    available_devices[list[t_x502_devrec]] - список устройств
                                    доступных к подключению 
                                    
    num_dev[int] - номер устройства 
    
    return hnd[t_x502_hnd]
    Описатель модуля 
    '''
    if num_dev >= len(available_devices):
        print("Номер устройства слишком большой")
        return None
    
    hnd = x502.X502_Create()
    ierr = x502.X502_OpenByDevRecord(hnd, ctypes.pointer(available_devices[num_dev]))
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    return hnd
    
    
def get_device_info(hnd):
    '''
    Получить информацию об подключенном устройстве
    
    hnd[t_x502_hnd] - Описатель модуля 
    '''
    info = structures.t_x502_info()
    
    ierr = x502.X502_GetDevInfo(hnd, ctypes.pointer(info))
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return
        
        
    print("Установлена связь со следующим модулем:")
    print(" Серийный номер:", info.SerNum.decode())
    print(" Наличие ЦАП: ", end='')
    if info.devflags & 1:
        print("Да")
    else:
        print("Нет")
    print(" Наличие BlackFin: ", end='')
    if info.devflags & 4:
        print("Да")
    else:
        print("Нет")
    print(" Наличие гальваноразвязки:" , end='')
    if info.devflags & 2:
        print("Да")
    else:
        print("Нет")
    print(" Индустриальное исп.     :" , end='')
    if info.devflags & 32778:
        print("Да")
    else:
        print("Нет")
    print(" Наличие интерф. PCI/PCIe:" , end='')
    if info.devflags & 1024:
        print("Да")
    else:
        print("Нет")
    print(" Наличие интерф. USB     :" , end='')
    if info.devflags & 256:
        print("Да")
    else:
        print("Нет")
    print(" Наличие интерф. Ethernet:" , end='')
    if info.devflags & 512:
        print("Да")
    else:
        print("Нет")
    print(f" Версия ПЛИС: {info.fpga_ver >> 8}.{int(bin(info.fpga_ver)[-8:], 2)}")
    print(" Версия PLDA:", info.plda_ver)
    if (info.mcu_firmware_ver != 0):
        print(" Версия прошивки ARM: {}.{}.{}.{}".format(
               (info.mcu_firmware_ver >> 24) & 0xFF,
               (info.mcu_firmware_ver >> 16) & 0xFF,
               (info.mcu_firmware_ver >>  8) & 0xFF,
               info.mcu_firmware_ver & 0xFF))
        

def set_param_channel(hnd, ch_num, ch_modes, ch_ranges, avg):
    '''
    Установка параметров для каналов АЦП
    
    hnd[t_x502_hnd] - Описатель модуля 
    
    ch_num[list[int]] - Номера физического канала АЦП, начиная с 0
             (0-15 для дифференциального режима,
              0-31 для режима с общей землей)
    
    ch_modes[list[int]] - Режим измерения канал АЦП
              (0 Измерение напряжения относительно общей земли
              1 Дифференциальное измерение напряжения
              2 Измерение собственного нуля)

    ch_ranges[list[int]] - Диапазон измерения канала
                0 - Диапазон +/-10V
                1 - Диапазон +/-5V
                2 - Диапазон +/-2V
                3 - Диапазон +/-1V
                4 - Диапазон +/-0.5V
                5 - Диапазон +/-0.2V
    
    avg[int] - Коэффициент усреднения по каналу. Нулевое значение
          соответствует значению коэффициента, определенного
          библиотекой. Для явного задания коэффициента усреднения
          нужно перед значение от 1 (отсутствие усреднения) до 128
    '''
    # Проверка на количество каналов
    if len(ch_num) != len(ch_modes) or len(ch_num) != len(ch_ranges):
        print("Списки параметров должны быть одинаковой длины")
        return None
    
    numbers = len(ch_num)
    
    ierr = x502.X502_SetLChannelCount(hnd, numbers)
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    for i in range(numbers):
        ierr = x502.X502_SetLChannel(hnd, i, ch_num[i], ch_modes[i], ch_ranges[i], avg)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None
    
    return None


def set_rate_adc_din(hnd, freq_adc, freq_frame, freq_din):
    '''
    Установка параметров для каналов АЦП и цифровых входов
    
    hnd[t_x502_hnd] - Описатель модуля
    
    freq_adc[double] - требуемое значения частоты сбора
                      АЦП в Герцах
    
    freq_frame[double] - ребуемое значение частоты сбора
                        кадров (частоты сбора на логический канал) АЦП
                        в Герцах

    freq_din[double] - требуемое значения частоты
                      синхронного вывода в Герцах
    
    return: freq_adc[double], freq_frame[double], freq_din[double] 
            установленные параматры частоты сбора 
    '''
    
    f_adc = ctypes.c_double(freq_adc)
    f_frame = ctypes.c_double(freq_frame)
    f_din = ctypes.c_double(freq_din)

    ierr = x502.X502_SetAdcFreq(hnd, ctypes.pointer(f_adc), ctypes.pointer(f_frame))
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return 0, 0, 0
    
    ierr = x502.X502_SetDinFreq(hnd, ctypes.pointer(f_din))
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return 0, 0, 0
    
    ierr = x502.X502_Configure(hnd, 0)
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return 0, 0, 0
    
    return f_adc.value, f_frame.value, f_din.value


def _fill_array_adc(n_ch, adc_data, first_lch, block_size):
    '''
    Вспомогательная функция, создаёт массив numpy, инициализарованный 
    нулями, размером n_ch X block_size / n_ch. Запоняет его по 
    каждому каналу
    
    n_ch[int] - Количество каналов 
    
    adc_data[c_array[double]] - Данные с АЦП
    
    first_lch[int] - Номер логического канала, к которому 
                     принадлежит первый отсчёт
    block_size[int] - Количество отсчётов со всех каналов 
                      АЦП
                      
    return: data_per_ch[array[array[double]]] 
            Данные с АЦП разбитые по каналам
    '''
    
    data_per_ch = zeros((n_ch, ceil(block_size / n_ch)))
    
    for i in range(first_lch.value, block_size + first_lch.value):
        data_per_ch[i % n_ch, i // n_ch] = adc_data[i]
        
    return data_per_ch
    

def read_adc_data(hnd, block_size, timeout, n_ch):
    '''
    Получение данных с АЦП
    
    hnd[t_x502_hnd] - Описатель модуля
    
    block_size[int] - Размер буфера, в который будут сохранены 
                      данные с АЦП
                      
    timeout[int] - Таймаут на прием данных в мс
    
    n_ch[int] - Количество каналов
    
    return: data_per_ch[array[array[double]]] 
            Данные с АЦП в Вольтах разбитые по каналам
    '''
    
    ierr = x502.X502_StreamsEnable(hnd, 1)
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    ierr = x502.X502_StreamsStart(hnd)
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    
    rcv_buf = (ctypes.c_uint32*block_size)() # Массив для данных из буфера
    din_data = (ctypes.c_uint32*block_size)() # Массив для данных цифрового входа
    adc_data = (ctypes.c_double*block_size)() # Массив для данных с АЦП
    
    rcv_size = x502.X502_Recv(hnd, rcv_buf, block_size, timeout)
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return din_data, adc_data
    
    # Получаем номер логического канала, которому соответствует первый отсчёт в массиве
    first_lch = ctypes.c_uint32()
    ierr = x502.X502_GetNextExpectedLchNum(hnd, ctypes.pointer(first_lch))
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    adc_size = ctypes.c_size_t(block_size)
    din_size = ctypes.c_size_t(block_size)
    
    ierr = x502.X502_ProcessData(hnd, rcv_buf, rcv_size, 1,
                       adc_data, ctypes.pointer(adc_size), din_data, ctypes.pointer(din_size))
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
       
    ierr  = x502.X502_StreamsStop(hnd)
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    data_per_ch = _fill_array_adc(n_ch, adc_data, first_lch, block_size)
    
    return data_per_ch


def write_dac_data_cycle(hnd, data_dac1, data_dac2, start_stream=True):
    '''
    Воспроизведение данных через ЦАП в циклическом режиме
    
    hnd[t_x502_hnd] - Описатель модуля
    
    data_dac1[list[double]] - Данные для первого канала
                              ЦАП
                              
    data_dac2[list[double]] - Данные для второго канала
                              ЦАП
    
    start_stream[bool] - Параметр отвечающи за запуск потока
                        в вызове функции
                        
    return None
    '''
    
    # Проверка доступности 
    # 48 - флаг для первого и второго канала
    ierr = x502.X502_StreamsEnable(hnd, 48) 
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    cnt_ch = 0
    
    # Подготовка данных для первого канала ЦАП
    if data_dac1 is None:
        dac1_arr = None
        
    elif len(data_dac1) > 0: 
        cnt_ch += 1
        dac1_arr = (ctypes.c_double * len(data_dac1))(*data_dac1)
        dac1_arr_len = len(dac1_arr)
        dac_arr_len = dac1_arr_len
    
    # Подготовка данных для второго канала ЦАП
    if data_dac2 is None:
        dac2_arr = None
        
    elif len(data_dac2) > 0:
        cnt_ch += 1
        dac2_arr = (ctypes.c_double * len(data_dac2))(*data_dac2)
        dac2_arr_len = len(dac2_arr)
        dac_arr_len = dac2_arr_len
        
    if cnt_ch == 2 and dac2_arr_len != dac1_arr_len:
        print("Размеры массивов должны быть одинаковыми")
        return None
    
    elif cnt_ch == 0:
        print("Нужно задать хоть какие-то данные")
        return None
    
    # Буфер слов передаваемоых в устройство
    buf_arr = (ctypes.c_uint32 * (dac_arr_len * cnt_ch))()
    
    # Выделяется место под циклический буфер на вывод
    ierr = x502.X502_OutCycleLoadStart(hnd, cnt_ch * dac_arr_len)
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
        
    # Подготовка данных в виде слов
    ierr = x502.X502_PrepareData(hnd, dac1_arr, dac2_arr, None,
                                 dac_arr_len, 3, buf_arr)
    
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
        
    # Передача слова
    snd_cnt = x502.X502_Send(hnd, buf_arr, dac_arr_len * cnt_ch, 500)
    if snd_cnt < 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    if snd_cnt < dac_arr_len * cnt_ch:
        print('Отправлены не все слова')
        return None
    
    # Делаем активным загруженный сигнал
    ierr = x502.X502_OutCycleSetup(hnd, 2)
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    if start_stream:
        # Запускаем поток, в котором данные выводятся
        ierr = x502.X502_StreamsStart(hnd)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None

        # Закрываем поток
        ierr = x502.X502_StreamsStop(hnd)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None
    
    
def write_dac_data(hnd, data_dac1, data_dac2, start_stream=True):
    '''
    Воспроизведение данных через ЦАП единожды
    
    hnd[t_x502_hnd] - Описатель модуля
    
    data_dac1[list[double]] - Данные для первого канала
                              ЦАП
                              
    data_dac2[list[double]] - Данные для второго канала
                              ЦАП
    
    start_stream[bool] - Параметр отвечающи за запуск потока
                        в вызове функции
                        
    return None
    '''
    
    # Проверка доступности 
    # 48 - флаг для первого и второго канала
    ierr = x502.X502_StreamsEnable(hnd, 48) 
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    cnt_ch = 0
    
    # Подготовка данных для первого канала ЦАП
    if data_dac1 is None:
        dac1_arr = None
        
    elif len(data_dac1) > 0: 
        cnt_ch += 1
        dac1_arr = (ctypes.c_double * len(data_dac1))(*data_dac1)
        dac1_arr_len = len(dac1_arr)
        dac_arr_len = dac1_arr_len
        
        # Устанавливаем начальное значение на первом канале ЦАП
        ierr = x502.X502_AsyncOutDac(hnd, 0, ctypes.c_double(dac1_arr[0]), 3)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None
    
    # Подготовка данных для второго канала ЦАП
    if data_dac2 is None:
        dac2_arr = None
        
    elif len(data_dac2) > 0:
        cnt_ch += 1
        dac2_arr = (ctypes.c_double * len(data_dac2))(*data_dac2)
        dac2_arr_len = len(dac2_arr)
        dac_arr_len = dac2_arr_len
        
        # Устанавливаем начальное значение на втором канале ЦАП
        ierr = x502.X502_AsyncOutDac(hnd, 1, ctypes.c_double(dac2_arr[0]), 3)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None
        
    if cnt_ch == 2 and dac2_arr_len != dac1_arr_len:
        print("Размеры массивов должны быть одинаковыми")
        return None
    
    elif cnt_ch == 0:
        print("Нужно задать хоть какие-то данные")
        return None
    
    # Буфер слов передаваемоых в устройство
    buf_arr = (ctypes.c_uint32 * (dac_arr_len * cnt_ch))()
    
    # Загрузка начальных значений в устройство
    ierr = x502.X502_PreloadStart(hnd)
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    # Подготовка данных в виде слов
    ierr = x502.X502_PrepareData(hnd, dac1_arr, dac2_arr, None,
                                 dac_arr_len, 3, buf_arr)
    if ierr != 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    # Передача слова
    snd_cnt = x502.X502_Send(hnd, buf_arr, dac_arr_len * cnt_ch, 500)
    if snd_cnt < 0:
        print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
        return None
    
    if snd_cnt < dac_arr_len * cnt_ch:
        print('Отправлены не все слова')
        return None
    
    if start_stream:
        # Запускаем поток, в котором данные выводятся
        ierr = x502.X502_StreamsStart(hnd)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None

        # Закрываем поток
        ierr = x502.X502_StreamsStop(hnd)
        if ierr != 0:
            print(f'Ошибка {ierr}, {errors.err_dict[ierr]}')
            return None
        
        
def sync_write_read(hnd, data_dac1, data_dac2, block_size, timeout, n_ch):
    '''
    Воспроизведение данных через ЦАП и 
    одновременное считывание данный с АЦП
    
    hnd[t_x502_hnd] - Описатель модуля
    
    data_dac1[list[double]] - Данные для первого канала
                              ЦАП
                              
    data_dac2[list[double]] - Данные для второго канала
                              ЦАП
                              
    block_size[int] - Размер буфера, в который будут сохранены 
                      данные с АЦП
                      
    timeout[int] - Таймаут на прием данных в мс
    
    n_ch[int] - Количество каналов
    
    return: data_per_ch[array[array[double]]] 
            Данные с АЦП в Вольтах разбитые по каналам
    '''
    
    write_dac_data(hnd, data_dac1, data_dac2, False)
    
    data_per_ch = read_adc_data(hnd, block_size, timeout, n_ch)
    
    return data_per_ch