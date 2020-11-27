"""
Class to calculate distance
SENSOR:  using the MaxBotix HRLV-EZ sensor.
Datasheet: https://www.maxbotix.com/documents/HRLV-MaxSonar-EZ_Datasheet.pdf
Model: MB1003
BLE/CPU: using Adafruit's ItsyBitsy nRF52840
Documentation: https://learn.adafruit.com/adafruit-itsybitsy-nrf52840-express/overview
BORROWED CODE FROM : An Adafruit Trinket learning guide for the Matbotix:
    https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/master/Trinket_Ultrasonic_Rangefinder/Trinket_Ultrasonic_Rangefinder.py
"""
import board
import pulseio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService


class MD_BLE:
    """[summary]
    """
    def __init__(self, pin=board.D13, sample_num=20, use_ble=False):
        # Might not want to use BLE, perhaps for testing purposes
        self.use_ble = use_ble
        self.sample_num = sample_num
        try:
            self.pulses = pulseio.PulseIn(pin, self.sample_num)
        except ValueError as e:
            raise ValueError(e)
        self.pulses.pause()

        # The samples list holds the readings that will be used in calculating the distance.  Pulse readings that
        # are determined to be way off (say 655355....) will not be included so len(samples) is <= sample_num.
        self.samples = []

        if self.use_ble:
            # Set up BLE based on Adafruit's CircuitPython libraries.
            self.ble = BLERadio()
            uart_service = UARTService()
            advertisement = ProvideServicesAdvertisement(uart_service)
            #  Advertise when not connected.
            self.ble.start_advertising(advertisement)

    def _get_samples(self):
        """ Internal.
            Uses the pulses instance created in __init__ to gather 'legitimate'
            pulse readings into the samples list.
        """
        print('--> _get_samples')
        # Empty the list containing previous samples.
        self.samples = []
        # Get pulse readings. (i.e.: Using pulse width method to detect distance.)
        self.pulses.clear()
        self.pulses.resume()
        # Wait until there are sample_num pulses.
        while len(self.pulses) < self.sample_num:
            pass
        self.pulses.pause()
        # Add 'legitimate' readings to the sample list.
        for i in range(self.sample_num):
            # According to the sensor's datarange, valid values are 300 to 5000.
            # Note: Values of 300 most likely mean the sensor is too close to the
            # object since objects must be at least 300mm from the sensor.
            print('{} pulse value: {}'.format(i, self.pulses[i]))
            # Using 301 because when testing we found occassionally readings
            # that should have been 300 would be 301.
            if self.pulses[i] > 301 and self.pulses[i] <= 5000:
                self.samples.append(self.pulses[i])
                print('valid: {}'.format(self.pulses[i]))
        if len(self.samples) == 0:
            raise Exception('None of the readings were in the 300mm to 5000mm range.')
    @property
    def mode(self):
        """
        Copied from Adafruit Learning Guide (see above for link).
        Then modified.

        find the mode (most common value reported)
        will return median (center of sorted list)
        should mode not be found
        """
        self.samples = sorted(self.samples)
        n = len(self.samples)
        print('number of samples is {}'.format(n))

        max_count = 0
        mode = 0
        bimodal = 0
        counter = 0
        index = 0

        while index < (n - 1):
            prev_count = counter
            counter = 0

            while (self.samples[index]) == (self.samples[index + 1]):
                counter += 1
                index += 1

            if (counter > prev_count) and (counter > max_count):
                mode = self.samples[index]
                max_count = counter
                bimodal = 0

            if counter == 0:
                index += 1

            # If the dataset has 2 or more modes.
            if counter == max_count:
                bimodal = 1

            # Return the median if there is no mode.
            if (mode == 0) or (bimodal == 1):
                print('using the median. mode: {} bimodal: {} '.format(mode, bimodal))
                mode = self.samples[int(n / 2)]

            return mode

    @property
    def distance(self):

        """ To be used by the caller.
        example:
            from MD_BLE import MD_BLE
            md = MD_BLE()
            distance_from_object = md.distance

        Returns:
            float: The distance from the object.
        """
        if self.use_ble:
            print("WAITING FOR BLE CONNECTION...")
            while not self.ble.connected:
                pass
        self._get_samples()
        return self.mode
