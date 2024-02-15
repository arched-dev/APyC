# APyC 

## Python Wrapper for the APC API 

The APyC library simplifies working with the APC courier API in Python, ensuring accurate data input through dataclasses. It's designed for easy querying of delivery addresses and managing deliveries and collections. With built-in validation, APyC reduces errors, making courier service integration efficient for developers.

### Suitable for:

*  querying delivery addresses for services available 
*  creating deliveries / collections

### Installation

First you need to clone the repository and then install the package:

```bash
git clone https://githuib.com/lewis-morris/apyc
cd apyc
pip install .
```

### Todo 

- [ ] create a method for generating the raw ZPL code / download the PDF to file
- [ ] track orders by reference/consignment number etc
- [ ] improve error handling
