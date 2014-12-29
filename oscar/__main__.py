from oscar import OscarServer

def main():
    s = OscarServer()
    while True:
        k = raw_input('Press q to quit.')
        if k == 'q':
            break

if __name__ == '__main__':
    main()
