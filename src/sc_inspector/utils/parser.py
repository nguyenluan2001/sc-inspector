import argparse

def parser()-> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A sample script demonstrating CLI parsing.")

    # 2. Add a required positional argument
    parser.add_argument("-f", "--filepath", help="The name of the file to process")

    # 5. Parse the arguments
    return parser.parse_args()
