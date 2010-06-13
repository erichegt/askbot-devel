svn checkout http://closure-library.googlecode.com/svn/trunk/ google-closure
mkdir google-closure/tools
mkdir google-closure/tools/compiler
cd google-closure/tools/compiler
wget http://closure-compiler.googlecode.com/files/compiler-latest.zip
unzip compiler-latest.zip
cd ../../..
mkdir google-closure/tools/soy
cd google-closure/tools/soy
wget http://closure-templates.googlecode.com/files/closure-templates-for-javascript-latest.zip
unzip closure-templates-for-javascript-latest.zip
cd ../../
