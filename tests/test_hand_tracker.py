# import cv2
# import sys
# import os

# # Add parent directory to path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from gesture_engine.hand_tracker import HandTracker
# import config


# def main():
#     # Initialize camera
#     cap = cv2.VideoCapture(config.CAMERA_INDEX)
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
#     cap.set(cv2.CAP_PROP_FPS, config.FPS)
    
#     # Initialize hand tracker
#     tracker = HandTracker()
    
#     print("Hand Tracker Test Started")
#     print("Press 'q' to quit")
    
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("Failed to grab frame")
#             break
        
#         # Flip frame horizontally for mirror effect
#         frame = cv2.flip(frame, 1)
        
#         # Detect hands and draw landmarks
#         frame = tracker.find_hands(frame, draw=True)
        
#         # Get hand info
#         hand_count = tracker.get_hand_count()
        
#         # Display info on frame
#         cv2.putText(frame, f"Hands Detected: {hand_count}", 
#                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
#                    1, config.COLOR_TEXT, 2)
        
#         if tracker.is_hand_detected():
#             handedness = tracker.get_handedness(0)
#             if handedness:
#                 cv2.putText(frame, f"Hand: {handedness}", 
#                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
#                            1, config.COLOR_TEXT, 2)
            
#             # Show landmark positions for index finger tip
#             index_tip_pos = tracker.get_specific_landmark(config.INDEX_TIP, 0)
#             if index_tip_pos:
#                 cv2.putText(frame, f"Index Tip: {index_tip_pos}", 
#                            (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 
#                            0.6, config.COLOR_TEXT, 2)
        
#         # Display the frame
#         cv2.imshow('Hand Tracker Test', frame)
        
#         # Exit on 'q' key
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
    
#     # Cleanup
#     tracker.close()
#     cap.release()
#     cv2.destroyAllWindows()
#     print("Hand Tracker Test Completed")


# if __name__ == "__main__":
#     main()
