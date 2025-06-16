"""
TODO
"""

from collections import deque
import datetime as dt
import threading
from typing import Tuple, Optional

################################################################################
################################################################################
################################################################################
class DutyCycleTimestamp:
    """
    TODO
    """
    ################################################################################
    def __init__(self, mytime : dt.datetime, value : bool ) -> None:
        """
        TODO
        """
        self.time = mytime
        self.value = value # This records what we change to at the specified time!
        return
    
    ################################################################################
    def __str__(self) -> str:
        """
        TODO
        """
        return f"{self.time.strftime('%H:%M:%S.%f')} : {self.value}"

    



################################################################################
################################################################################
################################################################################
class DutyCycle(threading.Thread):
    """
    TODO
    """
    time_step = 0.01
    # HERE IS THE TABLE FROM NANOMOTION FOR THE HR4 MOTORS
    # This has been simplified a bit - the maximum speed of a motor in the motor box
    # is 2000 encoders/s which is 10 mm/s. This effectively means we can neglect
    # looking at the velocity variation, and the force will be the determining factor
    # for which duty cycle we pick. The layout is 'letter' (as defined in the table),
    # the maximum force which should be applied by this particular cycle (interpolated
    # slightly to be the maximum force at 10 mm/s for safety), and then the time
    # allowed on and total cycle length for air and then vacuum.
    # A negative value means no duty cycle should be used.
    DUTY_CYCLE_HR4_DICT = {
    #    L  : FMAX  , AIR,             VACUUM
        'A' : [  1.7, [ -1.0,  -1.0 ], [  -1.0,  -1.0 ] ],
        'B' : [  5.0, [ -1.0,  -1.0 ], [ 184.0, 418.2 ] ],
        'C' : [  7.6, [ -1.0,  -1.0 ], [ 107.0, 411.5 ] ],
        'D' : [  9.7, [ -1.0,  -1.0 ], [  72.0, 423.5 ] ],
        'E' : [ 11.5, [ 87.0, 111.5 ], [  55.0, 423.1 ] ],
        'F' : [ 13.7, [ 62.0, 110.7 ], [  39.0, 433.3 ] ],
        'G' : [ 14.5, [ 56.0, 112.0 ], [  35.0, 437.5 ] ]
    }

    ################################################################################
    def __init__(self, force : float, environment : str) -> None:
        """
        TODO
        """
        # Fundamental properties of the duty cycle
        self.infinite_run_time = False
        self.time_allowed_on, self.total_cycle_length = self.get_duty_cycle_from_force_and_environment(force, environment)  # seconds
        print(self.time_allowed_on, self.total_cycle_length)
        if self.time_allowed_on < 0 or self.total_cycle_length < 0:
            self.infinite_run_time = True

        self.resume_cycle_after = 1.0 # seconds

        # Data management
        self.list_of_timestamps = deque()                 # Container for timestamps and status changes
        self.mav = 0.0                                    # The moving average of the motor's movement
        self.is_motor_moving_now = False                  # This is status of motor's movement right now
        self.motor_was_moving_at_cycle_beginning = False  # This is status one duty cycle's worth ago
        self.is_motor_movement_requested = False          # Indicates if the user has requested movement
        self.is_motor_resting = False                     # Indicates if the motor is resting

        # Other
        self.event = threading.Event() # Used for timeouts that can be cancelled
        self.lock = threading.Lock()   # Used to ensure data edited properly

        # Initialise
        super().__init__()
        return
    
    ################################################################################
    def run(self) -> None:
        """
        TODO
        """
        if self.infinite_run_time:
            return
        self.is_running = True
        ctr = 0
        rounding_digits = 2
        factor = float(10**rounding_digits)

        # Generate initial timestamp
        self.stop_motor_moving()

        # Start loop
        while self.is_running:
            # Get current time
            start_loop_time = dt.datetime.now()

            # GET THE LOCK FOR EDITING DATA
            self.lock.acquire() 
            
            # Update MAV if we have timestamps in play
            if len(self.list_of_timestamps) > 0:
                # Remove times from queue if needed
                if ( start_loop_time - self.list_of_timestamps[0].time ).total_seconds() > self.total_cycle_length:
                    self.motor_was_moving_at_cycle_beginning = self.list_of_timestamps[0].value
                    self.list_of_timestamps.popleft()

            # Calculate MAV
            if len(self.list_of_timestamps) > 0:
                self.mav = 0.0
                # Calculate in-between bits
                for i in range(0,len(self.list_of_timestamps) - 1):
                    if self.list_of_timestamps[i].value:
                        self.mav += ( self.list_of_timestamps[i+1].time - self.list_of_timestamps[i].time ).total_seconds()
                
                # Add to mav if we're currently moving
                if self.list_of_timestamps[-1].value:
                    self.mav += ( start_loop_time - self.list_of_timestamps[-1].time ).total_seconds()

                # Add to mav if previous status was TRUE
                if self.motor_was_moving_at_cycle_beginning:
                    self.mav += self.total_cycle_length - ( start_loop_time - self.list_of_timestamps[0].time ).total_seconds()

                # Round
                self.mav = int( self.mav*factor + 0.5 )/factor
            else:
                # Set MAV based on status - motor running 100%
                if self.motor_was_moving_at_cycle_beginning == True and self.is_motor_moving_now == True:
                    self.mav = self.total_cycle_length
                
                # Motor running 0%
                elif self.motor_was_moving_at_cycle_beginning == False and self.is_motor_moving_now == False:
                    self.mav = 0.0
                
                # Should not encounter this
                else:
                    raise ValueError("This value should not be possible. Examine code carefully!")

            # RELEASE THE LOCK AS WE'RE DONE EDITING
            self.lock.release()

            # Now check if mav exceeds limits - pause if so
            if self.mav >= self.time_allowed_on and self.is_motor_resting == False:
                self.is_motor_resting = True
                self.stop_motor_moving()
                print("Threshold exceeded. Pausing motor")
            
            # Check if we need to resume
            if self.mav <= self.time_allowed_on - self.resume_cycle_after and self.is_motor_resting:
                self.is_motor_resting = False
                if self.is_motor_movement_requested:
                    self.start_motor_moving()
                    print("Resuming movement")
                else:
                    print("Rest over, but not moving")

            # Sleep a bit
            ctr += 1
            if ctr % 25 == 0:
                print(self.is_motor_movement_requested, self.is_motor_moving_now, self.mav, start_loop_time.strftime('%H:%M:%S.%f'), ", ".join( [str(x) for x in self.list_of_timestamps] ))
            end_loop_time = dt.datetime.now()

            try:
                self.event.wait( timeout = self.time_step - (1e-6)*( end_loop_time - start_loop_time ).microseconds )
            except ValueError:
                print( f"Requesting sleep for negative time not allowed (time difference is {self.time_step} - {(1e-6)*( end_loop_time - start_loop_time ).microseconds})" )
                break
        
        return
    
    ################################################################################
    def start_motor_moving(self) -> None:
        """
        TODO
        """
        # Check if requested - don't do anything if it isn't
        if self.is_motor_movement_requested == False:
            return
        
        # Check if already moving - don't do anything if it is
        if self.is_motor_moving_now:
            return
        
        # Check if motor is currently paused
        if self.is_motor_resting == True:
            print("Motor movement has been requested, but motor currently paused. Will start when motor ready")
            return

        # Prevent editing by others
        self.lock.acquire()

        # Start moving motor
        self.is_motor_moving_now = True
        self.list_of_timestamps.append( DutyCycleTimestamp( dt.datetime.now(), True ) )
        
        # Allow editing by others
        self.lock.release()
        return
    
    ################################################################################
    def stop_motor_moving(self) -> None:
        """
        TODO
        """
        # Check if already stopped - don't do anything if it is
        if self.is_motor_moving_now == False:
            return
        
        # Allow editing
        self.lock.acquire()

        # Stop moving motor
        self.is_motor_moving_now = False
        self.list_of_timestamps.append( DutyCycleTimestamp( dt.datetime.now(), False ) )

        # Allow editing by others
        self.lock.release()
        return

    ################################################################################
    def request_motor_movement(self) -> None:
        self.is_motor_movement_requested = True
        self.start_motor_moving()
        return
    ################################################################################
    def tell_motor_to_stop(self) -> None:
        self.is_motor_movement_requested = False
        self.stop_motor_moving()
        return
    ################################################################################
    def kill_thread(self) -> None:
        """
        TODO
        """
        self.event.set()
        self.is_running = False
        return
    ################################################################################
    @staticmethod
    def get_duty_cycle_from_force_and_environment( force : float, environment : str ):
        """
        TODO
        """
        # Check environment
        if environment == 'air':
            index = 1
        elif environment == 'vacuum':
            index = 2
        else:
            # ERROR - assume no movement allowed
            print(f'\"{environment}\" is invalid. It needs to be \"air\" or \"vacuum\"')
            return [0, float('inf')]
        
        # Now get parameters
        for value in DutyCycle.DUTY_CYCLE_HR4_DICT.values():
            if force <= value[0]:
                print(value[index])
                return value[index]
        
        # Return error
        print('Force exceeds threshold. Will prevent motor\'s movement')
        return [0, float('inf')]
        



def main():
    d = DutyCycle(14.0, 'vacuum')
    d.start()
    while True:
        try:
            s = input('Press p and then enter\n')
            if s == 'p':
                if d.is_motor_movement_requested == True:
                    d.tell_motor_to_stop()
                else:
                    d.request_motor_movement()
            else:
                print("Not p")
            
            s = None
        except KeyboardInterrupt:
            d.kill_thread()
            break

    print(d.is_motor_moving_now)
    print(d.motor_was_moving_at_cycle_beginning)

    # a = DutyCycleTimestamp(datetime.now(),True)
    # b = DutyCycleTimestamp(datetime.now(), False)

    # c = [a,b]
    # print(", ".join([str(x) for x in c]))
        

if __name__ == '__main__':
    main()
