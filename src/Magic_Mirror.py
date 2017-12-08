import cv2
import numpy as np
import time
import random
from src import myUtills

def draw_text(frame, text, x, y, color=(255, 255, 255), thickness=20, size=5):
    if x is not None and y is not None:
        cv2.putText(
            frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, size, color, thickness)

def checkHandPosition(y,x):
    if (x>500 and x<687):
        return 3
        # if (y>131 and y<217):
        #     print("위쪽 화살표 클릭")
        #     return 0
        # elif (y>247 and y<364):
        #     print("첫번째 상자 클릭")
        #     return 1
        # elif (y>394 and y<511):
        #     print("두번째 상자 클릭")
        #     return 2
        # elif (y>541 and y<658):
        #     print("세번째 상자 클릭")
        #     return 3
        # elif (y>688 and y<774):
        #     print("아래쪽 화살표 클릭")
        #     return 4
        # return 100

def main():

    #cap = cv2.VideoCapture('video_2.mp4')
    cap = cv2.VideoCapture(1)

    # Random colors
    color = np.random.randint(0,255,(100,3))

    while(True):

        init_time = time.time()

        counter = 10  # 화면에 띄울 숫자
        end_time = init_time + counter + 1  # 타이머 끝나는 시간
        secondPassed = init_time + 1  # 1초가 지났는지 안지났는지 비교하는용

        timer_over = False  # 타이머 끝났는지 확인용

        #웹캠용
        left_hand = (200, 260)
        right_hand = (440, 260)
        left_foot = (260, 465)
        right_foot = (380, 465)

        # #video_3용
        # left_hand = (312, 610)
        # right_hand = (600, 430)
        # left_foot = (390, 940)
        # right_foot = (620, 950)



        while(cap.isOpened()):
            ret, frame = cap.read()
            print(frame.shape)

            dot_color = random.choice(color)
            frame = cv2.flip(frame, 1)  # 좌우반전
            frame = cv2.circle(frame, left_hand, 5, dot_color.tolist(), -1)
            frame = cv2.circle(frame, right_hand, 5, dot_color.tolist(), -1)
            frame = cv2.circle(frame, left_foot, 5, dot_color.tolist(), -1)
            frame = cv2.circle(frame, right_foot, 5, dot_color.tolist(), -1)

            if ret == True:
                center_x = int(frame.shape[1] / 20)
                center_y = int(frame.shape[0] / 3.8)

                if (time.time() < end_time):
                    draw_text(frame, str(counter), center_x, center_y)
                if (time.time() > secondPassed): # 1초가 지난 경우
                    counter -= 1
                    secondPassed += 1

                #frame = cv2.resize(frame, (360, 640))  # Resize image
                cv2.imshow('frame', frame)
                if (cv2.waitKey(1) & 0xFF == ord('q')) or (time.time() > end_time):
                    timer_over = True
                    break
            else:
                break


        # Lucas Kanade optical flow parameters
        lk_params = dict( winSize  = (15,15),
                           maxLevel = 2,
                           criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        ##Background UI 삽입
        back_img = cv2.imread('back_imgg.png')
        # back_img = cv2.resize(back_img, (640, 480))
        backgroundUI = myUtills.BitwiseImage(back_img)

        # Take first frame and find corners in it
        ret, old_frame = cap.read()
        old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)

        # Set tracking points
        p0 = np.array([ [list(left_hand)], [list(right_hand)],[list(left_foot)],[list(right_foot)]]) #tracking하는 포인트 위치와 개수 설정
        p0 = np.float32(p0)

        # Create a mask image for drawing purposes
        mask = np.zeros_like(old_frame)

        # body detector and overlayer

        body_detector = myUtills.detector()

        clothes_overlayer = myUtills.overlayer()
        right_overlayer = myUtills.arm_overlayer()
        pants_overlayer = myUtills.pants_overlayer()
        kindOfClothes = myUtills.listOfClothes().whatClothes

        countframe = 0

        # clothes managing
        clothesIndex = [0,1]  # 더미변수 (checkPosition 에서 받을 예정)
        top = []
        pants = []



        # 오버레이 루프
        while(True):
            countframe += 1
            if (countframe > 100000):
                countframe = 0
            if (countframe % 5000 == 0):
                # 1. optical flow
                ret, realframe = cap.read()
                realframe = cv2.flip(realframe, 1)  # 좌우반전


                frame_gray = cv2.cvtColor(realframe, cv2.COLOR_BGR2GRAY)

                # calculate optical flow
                p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
                # Select good points
                good_new = p1[st == 1]
                good_old = p0[st == 1]

                if (st.all() == 1):

                    # draw the tracks
                    for i, (new, old) in enumerate(zip(good_new, good_old)):
                        a, b = new.ravel()  # 현재 프레임의 좌표값
                        c, d = old.ravel()  # 이전 프레임의 좌표값
                        #checkHandPosition(a,b)
                        #print(a,b)
                        #mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)  # 현재와 이전의 프레임을 이어줌
                        realframe = cv2.circle(realframe, (a, b), 5, color[i].tolist(), -1)


                    # Now update the previous frame and previous points
                    old_gray = frame_gray.copy()
                    p0 = good_new.reshape(-1, 1, 2)

                # 2.detect body

                realframe = body_detector.detect_body2(realframe)
                box_coordinate = body_detector.box_coordinate

                # 3. check hand position and run actiom
                leftPosition = checkHandPosition(p1[0][0][1], p1[0][0][0])  # 왼손 위치 체크
                rightPosition = checkHandPosition(p1[1][0][1], p1[1][0][0])  # 오른손 위치 체크
                print("right hand position : ", rightPosition )

                clothesArrayIdx = 0

                if (leftPosition == 0 or rightPosition == 0):
                    # 위쪽 화살표 클릭
                    if (not clothesArrayIdx == 0):  # 0인 경우는 첫번째 배열이므로 더이상 위쪽으로 넘어갈 수 없음
                        clothesArrayIdx -= 1
                        backgroundUI = myUtills.BitwiseImage(cv2.imread('back_img2.png'))
                elif (leftPosition == 1 or rightPosition == 1):
                    # 첫번째 아이템 클릭
                    clothesIndex = [clothesArrayIdx, 0]
                elif (leftPosition == 2 or rightPosition == 2):
                    # 두번째 아이템 클릭
                    clothesIndex = [clothesArrayIdx, 1]
                elif (leftPosition == 3 or rightPosition == 3):
                    # 세번째 아이템 클릭
                    clothesIndex = [clothesArrayIdx, 2]
                elif (leftPosition == 4 or rightPosition == 4):
                    # 아래쪽 화살표 클릭
                    if (clothesArrayIdx < 2):  # 배열 크기가 1이므로 그 이상은 배열이 없으므로 더이상 아래로 내려갈 수 없음
                        clothesArrayIdx += 1
                        clothesIndex[0] = clothesArrayIdx
                        backgroundUI = myUtills.BitwiseImage(cv2.imread('back_img3.png'))

                # 4.overlay clothes

                print("left_h:",p1[0][0])
                print("right_h:",p1[1][0])
                print("left_f:", p1[2][0])
                print("right_f:", p1[3][0])



                #### overlay part start #####
                if len(clothesIndex) != 0 :
                    print(clothesIndex)

                    # 상하의 구분
                    if kindOfClothes[clothesIndex[0]][clothesIndex[1]] == 0 :  #0이면 상의, 1이면 하의
                        top = clothesIndex
                    elif kindOfClothes[clothesIndex[0]][clothesIndex[1]] == 1 :
                        pants = clothesIndex

                    # 입히기
                    if len(pants) != 0 :
                        realframe = pants_overlayer.overlay(realframe, box_coordinate, p1, pants)


                    if len(top) != 0 :
                        realframe = right_overlayer.overlay(realframe, box_coordinate, p1,top)  # 프레임, 얼굴좌표, (왼좌표. 오른좌표)
                        realframe = clothes_overlayer.overlay(realframe, box_coordinate, top)



                #### overlay part end ####

                #Background UI 삽입
                backgroundUI.setImage(realframe, 0, 0)

                if (st.all() == 1): # st == 1 이면 프레임 안
                    img = cv2.add(realframe, mask)


                #img = cv2.resize(img, (360, 640))  # Resize image
                cv2.imshow('frame', img)

                # 카메라 종료
                k = cv2.waitKey(30) & 0xff
                if k == 27:  # esc key
                    cap.release()
                    break

                # Detections

    cap.release()
    cv2.destroyAllWindows()




if __name__ == '__main__':
    main()