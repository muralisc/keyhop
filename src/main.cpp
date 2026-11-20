// Wired USB keyboard -> Bluetooth LE keyboard, 3 host slots.
// ESP32-S3: keyboard on USB host pins (GPIO19/20), BLE out.
//
// Slot switch:   Ctrl + Alt + 1 / 2 / 3          (left or right Ctrl/Alt, e.g. Right Ctrl + Right Alt)
// Re-pair slot:  Ctrl + Alt + Shift + 1 / 2 / 3  (forgets that slot's host)
// The chord is swallowed and never reaches the computer.
//
// Build for the board with -DBOARD_OLIMEX or -DBOARD_WAVESHARE (see platformio.ini).
// LED meanings are listed above updateLed().

#include <Arduino.h>
#include <Preferences.h>
// EspUsbHost (TinyUSB hid.h) must come before NimBLE: NimBLE's HIDTypes.h
// #defines names like HID_SUBCLASS_NONE that TinyUSB declares as enum members.
#include "EspUsbHost.h"
#include <NimBLEDevice.h>
#include <NimBLEHIDDevice.h>
#include <esp_system.h>
#if __has_include(<esp_mac.h>)
#include <esp_mac.h>
#endif

#if defined(BOARD_OLIMEX) == defined(BOARD_WAVESHARE)
#error "Define exactly one of BOARD_OLIMEX or BOARD_WAVESHARE"
#endif

constexpr uint8_t NUM_SLOTS = 3;
constexpr uint8_t LED_PIN = 38;  // Olimex: single green LED, active-low. Waveshare: RGB LED.

// Modifier bits in a boot keyboard report; left and right versions both count.
constexpr uint8_t MOD_CTRL = 0x01 | 0x10;   // Left Ctrl | Right Ctrl
constexpr uint8_t MOD_SHIFT = 0x02 | 0x20;  // Left Shift | Right Shift
constexpr uint8_t MOD_ALT = 0x04 | 0x40;    // Left Alt | Right Alt
constexpr uint8_t KEY_1 = 0x1E;  // HID usage for "1"; 2 and 3 follow

struct Report {
  uint8_t b[8];
};

static QueueHandle_t reportQueue;
static Preferences prefs;
static uint8_t currentSlot = 0;

static NimBLEServer *server = nullptr;
static NimBLEHIDDevice *hid = nullptr;
static NimBLECharacteristic *input = nullptr;
static volatile bool bleConnected = false;
static bool bleUp = false;
static uint32_t slotShownMs = 0;  // when the slot number blink started (Olimex LED)

// Standard boot-style keyboard: 8-byte input report, 1-byte LED output report.
static const uint8_t kReportMap[] = {
    0x05, 0x01, 0x09, 0x06, 0xA1, 0x01, 0x85, 0x01,
    0x05, 0x07, 0x19, 0xE0, 0x29, 0xE7, 0x15, 0x00, 0x25, 0x01,
    0x75, 0x01, 0x95, 0x08, 0x81, 0x02,
    0x95, 0x01, 0x75, 0x08, 0x81, 0x01,
    0x95, 0x05, 0x75, 0x01, 0x05, 0x08, 0x19, 0x01, 0x29, 0x05, 0x91, 0x02,
    0x95, 0x01, 0x75, 0x03, 0x91, 0x01,
    0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x25, 0x65,
    0x05, 0x07, 0x19, 0x00, 0x29, 0x65, 0x81, 0x00,
    0xC0};

// ---------- USB host side ----------

// Diagnostics shown on the LED (see updateLed()).
static volatile uint32_t lastKeyMs = 0;  // last parsed boot-keyboard report
static volatile uint32_t lastRawMs = 0;  // last data of any kind from the USB device

class UsbKeyboard : public EspUsbHost {
 public:
  void onReceive(const usb_transfer_t *transfer) override {
    if (transfer->status == USB_TRANSFER_STATUS_COMPLETED && transfer->actual_num_bytes > 0) {
      lastRawMs = millis();
    }
  }

  // Called from usbHost.task() in loop(); queue it so BLE work stays out of the USB callback.
  void onKeyboard(hid_keyboard_report_t report, hid_keyboard_report_t last_report) override {
    Report r;
    static_assert(sizeof(report) == 8, "unexpected HID report size");
    memcpy(r.b, &report, 8);
    lastKeyMs = millis();
    xQueueSend(reportQueue, &r, 0);
  }
};

static UsbKeyboard usbHost;

// ---------- BLE side ----------

class ServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer *s, ble_gap_conn_desc *desc) override {
    bleConnected = true;
  }
  void onDisconnect(NimBLEServer *s) override {
    bleConnected = false;
  }
  void onAuthenticationComplete(ble_gap_conn_desc *desc) override {
    // Remember who this slot is paired with, so re-pairing can forget them.
    String key = "peer" + String(currentSlot);
    prefs.putString(key.c_str(), NimBLEAddress(desc->peer_id_addr).toString().c_str());
  }
};
static ServerCallbacks serverCallbacks;

// Tag that tells several keyhops apart in Bluetooth lists: "keyhop <tag> <slot>".
// Default: 4 hex digits from this chip's factory MAC (unique per board, e.g. A3F2).
// Override per board at build time, up to 6 characters:
//   PLATFORMIO_BUILD_FLAGS='-DKEYHOP_TAG=\"desk\"' pio run -t upload
static const char *boardTag() {
#ifdef KEYHOP_TAG
  static_assert(sizeof(KEYHOP_TAG) - 1 <= 6, "KEYHOP_TAG must be 6 characters or fewer");
  return KEYHOP_TAG;
#else
  static char tag[5];
  if (!tag[0]) {
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);  // factory MAC, not changed by esp_base_mac_addr_set
    snprintf(tag, sizeof(tag), "%02X%02X", mac[4], mac[5]);
  }
  return tag;
#endif
}

static void startBle(uint8_t slot) {
  if (bleUp) {
    NimBLEDevice::deinit(true);  // bonds stay in flash; only RAM objects are freed
    bleUp = false;
    bleConnected = false;
    hid = nullptr;
    input = nullptr;
  }

  // Each slot presents a different Bluetooth address, so every computer
  // sees (and bonds with) a separate keyboard.
  uint8_t mac[6];
  esp_efuse_mac_get_default(mac);
  mac[5] = (uint8_t)(mac[5] + slot * 4);
  esp_base_mac_addr_set(mac);

  char name[16];
  snprintf(name, sizeof(name), "keyhop %s %u", boardTag(), slot + 1);
  NimBLEDevice::init(name);
  NimBLEDevice::setSecurityAuth(true, false, true);  // bonding, no MITM, secure connections
  NimBLEDevice::setSecurityIOCap(BLE_HS_IO_NO_INPUT_OUTPUT);

  server = NimBLEDevice::createServer();
  server->setCallbacks(&serverCallbacks, false);  // static object: NimBLE must not delete it on deinit

  hid = new NimBLEHIDDevice(server);
  input = hid->inputReport(1);
  hid->outputReport(1);
  hid->manufacturer()->setValue("DIY");
  hid->pnp(0x02, 0x1209, 0x0001, 0x0100);
  hid->hidInfo(0x00, 0x01);
  hid->reportMap((uint8_t *)kReportMap, sizeof(kReportMap));
  hid->startServices();
  hid->setBatteryLevel(100);

  NimBLEAdvertising *adv = server->getAdvertising();
  adv->setAppearance(0x03C1);  // keyboard
  adv->addServiceUUID(hid->hidService()->getUUID());
  adv->start();
  bleUp = true;
  slotShownMs = millis();

  Serial.printf("BLE up, slot %u, name \"%s\"\n", slot + 1, name);
}

static void sendReport(const uint8_t *b) {
  if (bleConnected && input) {
    input->setValue((uint8_t *)b, 8);
    input->notify();
  }
}

static void sendEmpty() {
  static const uint8_t empty[8] = {0};
  sendReport(empty);
}

// ---------- slot handling ----------

static void switchSlot(uint8_t s) {
  sendEmpty();  // release any keys still held on the old host
  currentSlot = s;
  prefs.putUChar("slot", s);
  startBle(s);
}

static void repairSlot(uint8_t s) {
  sendEmpty();
  String key = "peer" + String(s);
  String peer = prefs.getString(key.c_str(), "");
  if (peer.length() > 0 && bleUp) {
    NimBLEDevice::deleteBond(NimBLEAddress(std::string(peer.c_str())));
    prefs.remove(key.c_str());
  }
  currentSlot = s;
  prefs.putUChar("slot", s);
  startBle(s);
}

static void handleReport(const uint8_t *r) {
  static bool swallowing = false;
  uint8_t mods = r[0];

  bool empty = (mods == 0);
  for (int i = 2; i < 8; i++) {
    if (r[i]) empty = false;
  }

  // After a chord, ignore everything until all keys are released.
  if (swallowing) {
    if (empty) swallowing = false;
    return;
  }

  if ((mods & MOD_CTRL) && (mods & MOD_ALT)) {
    for (int i = 2; i < 8; i++) {
      uint8_t k = r[i];
      if (k >= KEY_1 && k < KEY_1 + NUM_SLOTS) {
        swallowing = true;
        uint8_t s = k - KEY_1;
        if (mods & MOD_SHIFT) {
          repairSlot(s);
        } else {
          switchSlot(s);
        }
        return;
      }
    }
  }

  sendReport(r);
}

// ---------- LED ----------

enum class UsbState { HostFailed, NoDevice, Unusable, Ready };

static UsbState usbState() {
  if (usbHost.clientHandle == nullptr) return UsbState::HostFailed;
  if (usbHost.deviceHandle == nullptr) return UsbState::NoDevice;
  if (!usbHost.isReady) return UsbState::Unusable;
  return UsbState::Ready;
}

#if defined(BOARD_OLIMEX)

// Single green LED, so everything is a blink pattern. Priority order:
//   1-3 quick blinks, pause   = slot number, shown for ~2 s after boot or a slot switch
//   very fast flicker         = USB host stack failed to start (firmware problem)
//   short blip every second   = no USB keyboard detected (wiring / power)
//   double blip every second  = USB device detected but unusable (e.g. hub inside it)
//   slow even blink           = keyboard OK, Bluetooth waiting to pair / connect
//   solid on                  = keyboard OK, Bluetooth connected
//   brief flick (inverted)    = a key report arrived from the keyboard
static void ledWrite(bool on) {
  digitalWrite(LED_PIN, on ? LOW : HIGH);  // active-low: GPIO low lights the LED
}

static void updateLed() {
  uint32_t now = millis();

  uint32_t t = now - slotShownMs;
  uint32_t blinkMs = (currentSlot + 1) * 300;
  if (t < blinkMs + 800) {
    ledWrite(t < blinkMs && (t % 300) < 150);
    return;
  }

  bool on;
  uint32_t p = now % 1000;
  switch (usbState()) {
    case UsbState::HostFailed:
      on = (now / 50) % 2 == 0;
      break;
    case UsbState::NoDevice:
      on = p < 100;
      break;
    case UsbState::Unusable:
      on = p < 100 || (p >= 250 && p < 350);
      break;
    default:
      on = bleConnected || p < 500;
      if (now - lastKeyMs < 60) on = !on;
      break;
  }
  ledWrite(on);
}

#else  // BOARD_WAVESHARE

// RGB LED. Priority order:
//   white flash  = keyboard report received and forwarded
//   red flash    = USB data received but not a boot-keyboard report
//   blue         = no USB device enumerated (overrides slot colour)
//   blue flicker = USB host stack failed to start
//   blue/white   = USB device enumerated but no usable interface (e.g. built-in hub)
//   slot colour  = keyboard detected, idle (slot 1 green, 2 blue, 3 magenta)
// Blinking = BLE advertising, solid = BLE connected.
static void updateLed() {
  static const uint8_t colors[NUM_SLOTS][3] = {{0, 30, 0}, {0, 0, 40}, {30, 0, 30}};
  static const uint8_t white[3] = {30, 30, 30}, red[3] = {40, 0, 0}, blue[3] = {0, 0, 40};
  uint32_t now = millis();
  const uint8_t *c = colors[currentSlot];
  bool on = bleConnected || ((now / 400) % 2 == 0);
  if (now - lastKeyMs < 100) {
    c = white;
  } else if (now - lastRawMs < 100) {
    c = red;
  } else if (usbHost.clientHandle == nullptr) {
    c = blue;  // USB host stack failed to start: fast flicker
    on = (now / 100) % 2 == 0;
  } else if (usbHost.deviceHandle == nullptr) {
    c = blue;  // nothing plugged in / not enumerating
  } else if (!usbHost.isReady) {
    c = ((now / 400) % 2 == 0) ? blue : white;  // device seen but unusable
    on = true;
  }
  neopixelWrite(LED_PIN, on ? c[0] : 0, on ? c[1] : 0, on ? c[2] : 0);
}

#endif

// ---------- serial diagnostics ----------

static void logUsbStateChanges() {
  static bool first = true;
  static UsbState last;
  UsbState s = usbState();
  if (!first && s == last) return;
  first = false;
  last = s;
  switch (s) {
    case UsbState::HostFailed: Serial.println("USB: host stack failed to start"); break;
    case UsbState::NoDevice:   Serial.println("USB: no device detected"); break;
    case UsbState::Unusable:   Serial.println("USB: device detected but no usable interface"); break;
    case UsbState::Ready:      Serial.println("USB: keyboard ready"); break;
  }
}

static void logReport(const uint8_t *r) {
  Serial.printf("key report: mods=%02X keys=%02X %02X %02X %02X %02X %02X%s\n",
                r[0], r[2], r[3], r[4], r[5], r[6], r[7], bleConnected ? "" : "  (BLE not connected, dropped)");
}

// ---------- Arduino ----------

void setup() {
  Serial.begin(115200);  // UART0 (GPIO43/44): Olimex USB-UART port; USB is busy being a host
#if defined(BOARD_OLIMEX)
  pinMode(LED_PIN, OUTPUT);
  ledWrite(false);
#endif
  Serial.printf("\nkeyhop starting, board tag %s\n", boardTag());
  prefs.begin("kb", false);
  currentSlot = prefs.getUChar("slot", 0);
  if (currentSlot >= NUM_SLOTS) currentSlot = 0;

  reportQueue = xQueueCreate(16, sizeof(Report));
  startBle(currentSlot);
  usbHost.begin();
}

void loop() {
  // This EspUsbHost version has no background task: it must be pumped here.
  // task() blocks ~1 tick on USB events, which also paces this loop.
  usbHost.task();

  Report r;
  while (xQueueReceive(reportQueue, &r, 0) == pdTRUE) {
    logReport(r.b);
    handleReport(r.b);
  }
  logUsbStateChanges();
  updateLed();
}
