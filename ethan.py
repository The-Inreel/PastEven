import cv2

frame = cv2.imread('saves/pastEven.png')

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 100, 200)

contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)

cv2.imshow('Objects', frame)

cv2.waitKey(0)

cv2.destroyAllWindows()