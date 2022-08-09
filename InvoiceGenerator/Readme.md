# Basic Invoice Pdf Generator 

## Usage Guide : -

cd into current folder
run `pip install -r requirement.txt`

test_configs.py contain csv_configuration for now, (tested in local with csv as data source)

to invoke run 'python invoice_generator.py' , by default it will take csv data in `static` directory and use html and 
css template from `templates` directory
result will be stored in output_dir
Note: 
The main code lies in invoice_generator.py ,

Future Scope: 
Only tested for csv at the moment.
will test postgres and excel version and make corrections soon


## Limitations : - 
Here the html to pdf converter is not perfect and has very less css support(doesn't support flex box used table to 
divide into two column partition) , other alternative packages with better support 
are available pdfkit or weasyprint, these were not chosen as they have external dependencies (can't resolve through pip )
thus avoided for simplicity of the project. 