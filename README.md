# pysharp

#WARNING DON'T EVER USE DEBUG MODE IF YOU ARE USING A FOR LOOP!

use
```
python3 pysharp.py -s main.pysharp
```

* im bored!

examples:

```
include stdlib

std::print("Watermelon shop!!!")
g = std::fetch("How many: ")

for i to std::int(g){
	std::printf("Watermelon Count:", i)
}
```

heres all the available functions and constants

```
fn std::print(arg){
	execute("print(arg)")
}

fn std::printf(prefix, arg){
	execute("print(prefix, arg)")
}

fn std::fetch(prompt){
	return execute("input(prompt)")
}

fn std::min(value1, value2){
	return execute("min(value1,value2)")
}

fn std::max(value1, value2){
	return execute("max(value1,value2)")
}

fn std::float(value){
	return execute("float(value)")
}

fn std::int(value1){
	return execute("int(value1)")
}

fn std::str(value){
	return execute("str(value1)")
}

fn std::rand(minval, maxval){
	return execute("random.randrange(int(minval),int(maxval))")
}

std::pi = execute("math.pi")
std::tau = 2 * std::pi
```

if statements

```
include stdlib

if std::tau / 2 == std::pi {
   std::print("Math proven")
}
```

for statement

my for statement starts at index 1 and moves up to a range

* my language doesnt support comments at the moment.
* also while loops
* list and any iterables
* doesnt support unary
* doesnt have dot notation for functions and attributes.

* if it syntax errors, just edit your soucre file until it works
* i havent really delved deep to error messages

```
range = 100

for var to range{
   std::print(var)
}
```
