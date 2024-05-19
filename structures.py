import ctypes

class t_x502_devrec_inptr(ctypes.Structure):
    '''
    Непрозрачная структура с информацией, достаточной для установления
    с ним связи. Зависит от типа устройства, интерфейса подключения и не
    доступна пользователю напрямую, а используется библиотекой в
    X502_OpenByDevRecord()
    '''
    pass 


class t_x502_location_type(ctypes.c_uint8):
    pass

class t_x502_dev_flags(ctypes.c_uint32):
    pass

class t_x502_devrec(ctypes.Structure):
    """
    Структура, описывающая устройство, по которой с ним можно установить соединение
    
    sign - Признак действительной структуры. Если запись действительна
    (соответствует какому-либо устройству), то должен быть равен #X502_DEVREC_SIGN
    
    devname - Название устройства
    
    serial - Серийный номер
    
    location - Описание подключения (если есть) 
    
    flags - флаги из #t_x502_dev_flags, описывающие устройство
    
    iface - Интерфейс, по которому подключено устройство
    
    location_type - Определяет, что именно сохранено в поле location
                    (одно значение из #t_x502_location_type)
    
    res - Резерв
    
    internal - Непрозрачный указатель на структуру с дополнительной информацией,
                необходимой для открытия устройства
                
    """
    _fields_ = [("sign", ctypes.c_uint32), 
                ("devname", ctypes.c_char * 32),
                ("serial", ctypes.c_char * 32),
                ("location", ctypes.c_char * 64),
                ("flags", t_x502_dev_flags),
                ("iface", ctypes.c_uint8),
                ("location_type", t_x502_location_type),
                ("res", ctypes.c_char * 122),
                ("internal", ctypes.POINTER(t_x502_devrec_inptr))]
    
    
class t_x502_hnd(ctypes.Structure):
    '''
    Непрозрачный указатель на структуру,
    содержащую информацию о настройках модуля и текущем соединении с ним.
    Пользовательской программе не доступны поля структуры напрямую, а только
    через функции библиотеки.
    Функции управления модулем принимают описатель модуля своим первым параметром.
    Описатель модуля создается с помощью X502_Create() и в конце работы
    освобождается с помощью X502_Free()
    '''
    pass 


class t_x502_cbr_coef(ctypes.Structure):
    '''
    Структура содержит калибровочные значения смещения нуля и коэффициента
    шкалы для одного диапазона АЦП или ЦАП.Результирующее значение АЦП
    вычисляется как (val - offs) * k, где val - неоткалиброванное значение
    '''
    _fields_ = [("offs", ctypes.c_double),
                ("k", ctypes.c_double)]
    
    
class t_x502_cbr(ctypes.Structure):
    '''
    Структура, содержащая все калибровочные коэффициенты, которые
    используются модулем L-502/E-502 */
    '''
    _fields_ = [("adc", t_x502_cbr_coef * 6),
                ("res1", ctypes.c_uint32 * 64),
                ("dac", t_x502_cbr_coef * 2),
                ("res2", ctypes.c_uint32 * 20)]
    
    
class t_x502_info(ctypes.Structure):
    '''
    Структура, содержащая постоянную информация о модуле L-502/E-502, которая как правило
    не изменяется после открытия
    
    name - Название устройства ("L502" или "E502")
    
    serial - Серийный номер
    
    devflags - Флаги из #t_x502_dev_flags, описывающие наличие
                в модуле определенных опций
    
    fpga_ver - Версия ПЛИС (старший байт - мажорная, младший - минорная)
    
    plda_ver - Версия ПЛИС, управляющего аналоговой частью
    
    board_rev - Ревизия платы
    
    mcu_firmware_ver - Версия прошивки контроллера Cortex-M4. Действительна только для модуля E-502
    
    factory_mac - Заводской MAC-адрес --- действителен только для
                  устройств с Ethernet-интерфейсом
    
    res - Резерв
    
    cbr - Заводские калибровочные коэффициенты (из Flash-памяти)
    '''
    _fields_ = [('BrdName', ctypes.c_char*32),
                ('SerNum', ctypes.c_char*32),
                ('devflags', ctypes.c_uint32),
                ('fpga_ver', ctypes.c_uint16),
                ('plda_ver', ctypes.c_uint8),
                ('board_rev', ctypes.c_uint8),
                ('mcu_firmware_ver', ctypes.c_uint32),
                ('factory_mac', ctypes.c_uint8*6),
                ('rezerv', ctypes.c_uint8*110),
                ('cbr', t_x502_cbr)]
    
    