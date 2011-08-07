PROTOCOL SPEC:

Currently, the server listens to the client and responds to certain messages. Originally my idea was to have all messages consisting of a header followed by a body (where the header would specify the number of bytes in the body, among other things where necessary). However, when me and xray worked out how to use variable length headers and put pretty much any kind of data in them, they became useful enough on their own to almost do away with bodies completely and now most messages consist only of a "header".
As of this commit, headers are structured thusly:

header: <typebyte><0byte><args><255byte> | <typebyte><255byte>
xbyte: a single byte representing x in range 0 <= n <= 255 as an unsigned int.
args: <arg> | <arg><args>
arg: <string><0byte>


example headers:

<3byte><0byte>'5'<0byte><255byte>
where 3byte is the type indicator byte 00000011 (generated in python as an ASCII char using chr(3)), '5' is the string '5', and <255byte> is 11111111 (chr(255)).

<5byte><0byte>'C:\\Users\\Philip\\python\\cryptobox\\frog - Copy.jpg'<0byte><255byte>
is another header with just one arg

<4byte><0byte>'C:\\Users\\Philip\\python\\cryptobox\\READ ME- Copy - Copy.txt'<0byte>'132'<0byte><255byte>
is a header with two args

Those headers can be written more concisely like this:
3,5,|
5,'C:\\Users\\Philip\\python\\cryptobox\\frog - Copy.jpg',|
4,'C:\\Users\\Philip\\python\\cryptobox\\READ ME- Copy - Copy.txt',132,|
Substituting printable characters (, and |) for 0byte and 255byte respectively.

Headers can be constructed easily using the makeheader function. The above headers would be:
makeheader(3,5)
makeheader(5,'C:\\Users\\Philip\\python\\cryptobox\\frog - Copy.jpg')
makeheader(4,'C:\\Users\\Philip\\python\\cryptobox\\READ ME- Copy - Copy.txt',132)

Note that although headers are strings, ints and floats can be passed to makeheader and will be converted to string form using str().

Headers are received almost exclusively by the server using the function receive_header. Receive_header calls recv(1) continuously, appending the characters it receives to an initially empty string, until it receives a 255byte. Then, it converts the type byte (first byte in header) back to an int using ord(header[0]), then it splits the remainder up using 0byte as the delimiter, and packs any args into a list. It then returns (type,args) (where args is [] if the header contains no args).

This somewhat complex mechanism exists to make it very easy for the client to call functions remotely on the server. The previously unexplained type byte maps to a function as defined in the serverside dictionary:

handlers = {
        1:authenticate,
        2:new_account,
        3:handle_send_request,
        4:receive_file,
        5:delete_file
        }

This allows those functions to be called serverside nice and simply: 

TYPE, args = receive_header(sock)
handlers[TYPE](sock,*args)

To request a file send, do:
message = makeheader(3,<GenerousEstimateOfFileSize>)
socket.send(message)
then wait for a reply from the server.
To tell the server to delete a file, do
message = makeheader(5,<filepath>)
socket.send(message)

In this way, the whole client-server communication mechanism is based around the client calling functions on the server.

There are currently two headers that precede bodies: header1 (authenticate) and header2 (new_account) and header4 (receive_file). header1 was made way back when I thought I'd use fixed-length headers and will soon be changed so as not to need a body. header2 will probably be deleted anyway because we'll be using PHP for new accounts. header4's body is an encryted file that the server must store (the header itself indicates how many bytes long this body is).

The entire spec for calling server functions from the client, is as follows:

1|				authenticate - server will receive 128 bytes of email and passhash and authenticate
2|				new_account (deprecated)
3,<estimatedfilesize>,|		handle_send_request - server will reply with chr(1) if there is enough room
4,<filepath>,<exactsize>,|	receive_file - server will recv exactsize bytes of ciphertext and store them at filepath
5,<filepath>,|			delete_file - server will delete the file at <filepath>
6,<oldpath>,<newpath>,|		move_file - this function doesn't exist on the server yet but will do some day
7,<oldpath>,<newpath>,|		rename_file - this function doesn't exist on the server yet but will do some day