# pysharp

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
