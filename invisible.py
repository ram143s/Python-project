import cv2
import numpy as np
import os
import glob

class InvisibilityCloak:
    def __init__(self):
        self.cap = None
        self.background = None
        self.color_ranges = {
            'red': [
                (np.array([0, 80, 20]), np.array([10, 255, 255])),
                (np.array([160, 80, 20]), np.array([180, 255, 255]))
            ],
            'blue': [
                (np.array([100, 50, 50]), np.array([130, 255, 255]))
            ],
            'green': [
                (np.array([40, 50, 50]), np.array([80, 255, 255]))
            ],
            'yellow': [
                (np.array([20, 100, 100]), np.array([30, 255, 255]))
            ],
            'orange': [
                (np.array([10, 100, 100]), np.array([20, 255, 255]))
            ],
            'purple': [
                (np.array([130, 50, 50]), np.array([160, 255, 255]))
            ]
        }
        self.current_color = 'red'
        self.backgrounds = []
        self.current_bg_index = 0
        self.frame_width = 640
        self.frame_height = 480
        
    def initialize_camera(self):
        """Initialize camera and get frame dimensions"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Error: Could not open webcam")
                return False
            
            # Get actual frame dimensions
            ret, test_frame = self.cap.read()
            if ret and test_frame is not None:
                self.frame_height, self.frame_width = test_frame.shape[:2]
                print(f"✅ Camera initialized: {self.frame_width}x{self.frame_height}")
                return True
            else:
                print("❌ Error: Could not read from webcam")
                return False
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            return False
        
    def load_backgrounds(self):
        """Load all background images from backgrounds folder"""
        bg_folder = "backgrounds"
        if not os.path.exists(bg_folder):
            os.makedirs(bg_folder)
            print(f"📁 Created '{bg_folder}' folder. Add your background images there.")
            
        # Load images
        img_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        for ext in img_extensions:
            self.backgrounds.extend(glob.glob(os.path.join(bg_folder, ext)))
            
        # Always add static option
        self.backgrounds.append('static')
        print(f"📸 Found {len(self.backgrounds)-1} background images + static capture")
        
    def create_default_background(self):
        """Create a default background"""
        # Create a nice gradient background
        background = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        for i in range(self.frame_height):
            color_value = int(50 + (i / self.frame_height) * 100)
            background[i, :] = [color_value, color_value//2, color_value//3]
            
        return background
        
    def capture_background(self):
        """Capture static background with better error handling"""
        if self.cap is None or not self.cap.isOpened():
            print("❌ Camera not available for background capture")
            return False
            
        print("\n🎯 Position yourself outside the camera view...")
        print("📸 Capturing background in 3 seconds...")
        
        try:
            for i in range(3, 0, -1):
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print(f"⚠️ Warning: Frame {4-i} failed, continuing...")
                    continue
                    
                cv2.putText(frame, f"Capturing in {i}...", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Background Capture", frame)
                cv2.waitKey(1000)
                
            # Capture the actual background
            for attempt in range(5):  # Try 5 times
                ret, background = self.cap.read()
                if ret and background is not None:
                    self.background = background.copy()
                    cv2.destroyWindow("Background Capture")
                    print("✅ Background captured successfully!")
                    return True
                    
            print("❌ Failed to capture background after multiple attempts")
            cv2.destroyWindow("Background Capture")
            return False
            
        except Exception as e:
            print(f"❌ Error during background capture: {e}")
            cv2.destroyAllWindows()
            return False
            
    def get_current_background(self):
        """Get current background with comprehensive error handling"""
        try:
            if self.backgrounds[self.current_bg_index] == 'static':
                if self.background is not None:
                    bg = cv2.resize(self.background, (self.frame_width, self.frame_height))
                else:
                    print("⚠️ No static background, using default")
                    bg = self.create_default_background()
            else:
                # Load image background
                bg_path = self.backgrounds[self.current_bg_index]
                bg_img = cv2.imread(bg_path)
                
                if bg_img is not None:
                    bg = cv2.resize(bg_img, (self.frame_width, self.frame_height))
                else:
                    print(f"⚠️ Could not load {bg_path}, using default")
                    bg = self.create_default_background()
                    
            return bg
            
        except Exception as e:
            print(f"⚠️ Error getting background: {e}, using default")
            return self.create_default_background()
            
    def create_color_mask(self, hsv_frame):
        """Create mask for the selected color"""
        try:
            mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
            
            for lower, upper in self.color_ranges[self.current_color]:
                color_mask = cv2.inRange(hsv_frame, lower, upper)
                mask = cv2.bitwise_or(mask, color_mask)
                
            # Clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            return mask
        except Exception as e:
            print(f"⚠️ Error creating mask: {e}")
            return np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
            
    def display_controls(self, frame):
        """Display control instructions on frame"""
        try:
            controls = [
                f"Color: {self.current_color.upper()}",
                f"Background: {os.path.basename(self.backgrounds[self.current_bg_index])}",
                "1-6: Colors | B: Background | C: Capture | Q: Quit"
            ]
            
            for i, text in enumerate(controls):
                y_pos = 30 + i * 25
                cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (255, 255, 255), 2)
                cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 0, 0), 1)
        except Exception as e:
            print(f"⚠️ Error displaying controls: {e}")
            
    def run(self):
        """Main application loop with comprehensive error handling"""
        print("""
🧙‍♂️ ===============================================
   ENHANCED INVISIBILITY CLOAK
   - Detect ANY color (Red, Blue, Green, Yellow, Orange, Purple)
   - Multiple backgrounds
   - Real-time switching
===============================================

🎮 Controls:
   1-6: Change color detection
   B: Switch background  
   C: Capture new background
   Q: Quit
        """)
        
        # Initialize everything
        if not self.initialize_camera():
            return
            
        self.load_backgrounds()
        
        # Try to capture initial background
        print("\n🎯 Let's capture your initial background...")
        if not self.capture_background():
            print("⚠️ Using default background instead")
            
        print("\n🎬 Starting invisibility cloak...")
        print("🎯 Hold up a colored cloth and press keys to change detection!")
        
        frame_count = 0
        
        while True:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("❌ Error reading from webcam")
                    break
                    
                frame_count += 1
                
                # Get current background
                background = self.get_current_background()
                
                # Ensure both images have same size
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                # Convert to HSV for color detection
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Create mask for selected color
                mask = self.create_color_mask(hsv)
                
                # Apply invisibility effect
                mask_normalized = mask.astype(float) / 255
                mask_3channel = np.stack([mask_normalized] * 3, axis=-1)
                
                # Blend frame and background
                final_output = frame.astype(float) * (1 - mask_3channel) + background.astype(float) * mask_3channel
                final_output = np.clip(final_output, 0, 255).astype(np.uint8)
                
                # Display controls
                self.display_controls(final_output)
                
                # Show result
                cv2.imshow("🧙‍♂️ Enhanced Invisibility Cloak", final_output)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('1'):
                    self.current_color = 'red'
                    print("🔴 RED detection")
                elif key == ord('2'):
                    self.current_color = 'blue'
                    print("🔵 BLUE detection")
                elif key == ord('3'):
                    self.current_color = 'green'
                    print("🟢 GREEN detection")
                elif key == ord('4'):
                    self.current_color = 'yellow'
                    print("🟡 YELLOW detection")
                elif key == ord('5'):
                    self.current_color = 'orange'
                    print("🟠 ORANGE detection")
                elif key == ord('6'):
                    self.current_color = 'purple'
                    print("🟣 PURPLE detection")
                elif key == ord('b'):
                    self.current_bg_index = (self.current_bg_index + 1) % len(self.backgrounds)
                    bg_name = os.path.basename(self.backgrounds[self.current_bg_index])
                    print(f"🖼️ Background: {bg_name}")
                elif key == ord('c'):
                    print("\n📸 Capturing new background...")
                    if self.capture_background():
                        print("✅ New background captured!")
                    else:
                        print("❌ Background capture failed")
                        
            except Exception as e:
                print(f"⚠️ Error in main loop: {e}")
                continue
                
        # Cleanup
        try:
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            print("\n👋 Thanks for using the Enhanced Invisibility Cloak!")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        cloak = InvisibilityCloak()
        cloak.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your webcam connection and try again.")