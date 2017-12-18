all: CFLAGS += $(shell pkg-config --cflags libadq) -DLINUX
all: LIBS += $(shell pkg-config --libs libadq)
all: adqapitwounitsmultirecord
debug: CFLAGS += $(shell pkg-config --cflags libadq) -DLINUX
debug: LIBS += $(shell pkg-config --libs libadq)

local: CFLAGS += -DLINUX
local: LIBS += -ladq -ludev -lpthread -lstdc++
local:ADQAPI_two_units_multirecord.c
	$(CXX) $(CFLAGS) -I../../Release -o adqapitwounitsmultirecord ADQAPI_two_units_multirecord.c -L../../source/.libs $(LIBS)

debug:ADQAPI_two_units_multirecord.c
	$(CXX) $(CFLAGS) -g -o adqapitwounitsmultirecord ADQAPI_two_units_multirecord.c $(LIBS)

adqapitwounitsmultirecord:ADQAPI_two_units_multirecord.c
	$(CXX) $(CFLAGS) -o adqapitwounitsmultirecord ADQAPI_two_units_multirecord.c $(LIBS)

clean:
	rm -f adqapitwounitsmultirecord
