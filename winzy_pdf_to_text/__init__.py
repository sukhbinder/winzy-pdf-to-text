import winzy
import pypdf


def pdf_to_text(file_path, page_range=None):
    """Convert PDF to text"""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        pages = [page.extract_text() for page in reader.pages]
        
        if page_range:
            if "-" in page_range:
                start, end = map(int, page_range.split('-'))
            else:
                start = end = int(page_range)
            return '\n'.join(pages[start-1:end])
        else:
            return '\n'.join(pages)
        

def create_parser(subparser):
    parser = subparser.add_parser("pdf2txt", description="Extract text from a given pdf")
    # Add subprser arguments here.
    parser.add_argument('file_path', type=str, help='Path to the PDF file')
    parser.add_argument('-p', '--pages', type=str, nargs='+', help='Page numbers to extract example: 1-4 for  1 to 4. or just a single page')
    
    return parser


class HelloWorld:
    """ An example plugin """
    __name__ = "pdf2txt"

    @winzy.hookimpl
    def register_commands(self, subparser):
        parser = create_parser(subparser)
        parser.set_defaults(func=self.run)

    def run(self, args):
        if args.pages:
            print(pdf_to_text(args.file_path, ','.join(args.pages)))
        else:
            print(pdf_to_text(args.file_path))
    
    def hello(self, args):
        # this routine will be called when "winzy "pdf2txt is called."
        print("Hello! This is an example ``winzy`` plugin.")

pdf2txt_plugin = HelloWorld()
