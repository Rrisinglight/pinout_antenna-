# Isabella — baseboard CM4

Baseboard для Raspberry Pi CM4. Текущая распайка 40-pin: [rpi4_hat_pinout_v4.html](rpi4_hat_pinout_v4.html).


| Модуль                                                                                                                                                             | Для чего                                                                                                                                                                                              | Интерфейс                                                  | Характеристики                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------- |
| [Matek I2C-INA-BM](https://www.mateksys.com/?portfolio=i2c-ina-bm) ([розница](https://rccopter.ru/product/modul-matek-ultra-precise-i2c-power-monitor-i2c-ina-bm)) | Понимать напряжение и ток батареи                                                                                                                                                                     | I2C1                                                       | INA228; 0–85 В, до 150 А, шунт 200 мкОм; адрес 0x45/0x44/0x41; JST-GH           |
| ADS1115                                                                                                                                                            | АЦП для получения RSSI с приёмников                                                                                                                                                                   | I2C1                                                       | 16 бит, 4 канала; адрес 0x48–0x4B                                               |
| [Beitian BK-450](https://www.beitian.com/en/sys-pd/856.html)                                                                                                       | GPS + компас + барометр, понимать относительную высоту антенны, положение и направление. Для удешевления можно распаять компас RM3100, барометр MS5611-01BA03, и GPS + LTE(наш модем) на самой плате. | UART3                                                      | Сейчас стоит: u-blox M9, NMEA/UBX; 5 В / 25 мА; встроенная антенна; выход 1PPS; |
| 2× Waveshare ST3025 через [Bus Servo Adapter (A)](https://www.waveshare.com/wiki/Bus_Servo_Adapter_(A))                                                            | Сервоприводы 2× Waveshare [ST3025](https://www.waveshare.com/wiki/ST3025_Servo?srsltid=AfmBOopBaKAc0qGLz79diYXxir3yMZYC1P3Ed8eZNa_OnVYHwqsTZ3Vu)                                                      | UART5                                                      | 12 В; 40 кг·см; стоп-ток 4,4 А каждый; шина 1 Мбит/с, телеметрия по позиции     |
| [TBS Crossfire TX](https://www.team-blacksheep.com/products/prod:crossfire_tx)                                                                                     | Передатчик управления TX №1, [CRSF](https://github.com/tbs-fpv/tbs-crsf-spec/blob/main/crsf.md)                                                                                                       | UART0 single-wire half-duplex + 2 GPIO направления         | до 2 Вт RF; питание 3,5–12,6 В; потребление до 3,2 Вт                           |
| [RadioMaster Nomad](https://radiomasterrc.com/products/nomad-dual-1-watt-gemini-xrossband-expresslrs-module)                                                       | Передатчик управления TX №2, условно ELRS                                                                                                                                                             | второй такой же UART + 2 GPIO направления                  | ExpressLRS dual-band 2,4 ГГц + 900 МГц, 2×1 Вт; XT30, 6–16,8 В                  |
| RX1264 / RX3364 PRO / MM238RW                                                                                                                                                             | приём аналогового видео 1,2 / 3,3 / 5,8 ГГц                                                                                                                                                                       | выходы CVBS, RSSI                | по 2 штатных приёмника на диапазон + место под третий (базово 6, максимум 9)                                              |
| [Haiwei K7](https://www.hwcodec.com/products/Mini-Encoder-Board/k7-h265h264-sdi-cvbs-encoder.html)                                                                 | кодирование видео в IP-поток                                                                                                                                                                          | вход CVBS (один) и SDI; выход Ethernet                     | H.265/H.264 до 1080p60; RTSP/RTMP/SRT/UDP; задержка 80–100 мс; 55×45 мм         |
| [LNK-SM004](https://www.e-linkchina.com.cn/products/show-503.html)                                                                                                 | Ethernet-свитч                                                                                                                                                                                        | Ethernet ×4: CM4, энкодер, IP-камера, порт для внешнего ПК | 100 Мбит/с; 38×38×7 мм                                                          |
| Вентилятор                                                                                                                                                         | охлаждение                                                                                                                                                                                            | PWM0                                                       | 12 вольт                                                                        |




## Интерфейсы и порты

- 4× UART: GPS, шина сервоприводов, 2× CRSF. CRSF — single-wire half-duplex: каждому каналу инвертор и 2 GPIO управления направлением.
- I2C: шина для АЦП, монитора батареи и компаса GPS.
- Видео, три диапазона: 1,2 ГГц — RX1264, 3,3 ГГц — RX3364 PRO, 5,8 ГГц — MM238RW. На каждый диапазон два штатных приёмника + посадочное место под третий: базово 6, максимум 9. Коммутация CVBS на один вход энкодера; управление приёмниками по SPI (общие DATA/CLK, индивидуальные CS); RSSI каждого приёмника — на АЦП.
- Опционально — чип analog→MIPI на плате. Кандидаты: [Axera XS9915](https://axera-tech.com/) — 4 входа AHD/TVI/CVI/CVBS, MIPI CSI-2 до 4 lane, QFN88; [ROHM/LAPIS ML86112](https://www.rohm.com/lapis-tech/product/video/ml86112) — 4 входа CVBS (один канал за раз), MIPI CSI-2 1 lane или BT.656, WQFN32; [Renesas RAA278842](https://www.renesas.com/en/products/raa278842) — 4 входа CVBS, MIPI CSI-2 4 lane, LQFP128.
- Разъём CSI под камеру со шлейфом.
- 2× внешних USB-разъёма.
- Ethernet: порт либо полноценный свитч на 5 потребителей (CM4, энкодер, IP-камера, внешний ПК, оптика); компактный конвертер оптика↔Ethernet.
- M.2 под NVMe SSD на PCIe, форматы 2242/2280 — как на [baseboard Orange Pi CM4](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-CM4-2.html).
- Питание: независимые ключи полного перезапуска линий 5 В и 12 В; отдельный ключ питания каждого TX-модуля с перезапуском по питанию; BEC 12 В держит оба серво на пределе (8,8 А для пары ST3025) плюс оба TX-модуля; PWM вентилятора.



## Вопросы

1. Серво: ST3025 или ST3215? Определяет мощность BEC 12 В.
2. Батарея: сколько S?
3. BK-450: распиновка 6-pin разъёма и состав интерфейсов (UART / I2C / CAN)?
4. Haiwei K7: напряжение питания и потребление — в открытых материалах не опубликованы.

