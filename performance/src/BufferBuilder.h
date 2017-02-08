/*
 * BufferBuilder.h
 *
 *  Created on: 7 Feb 2017
 *      Author: gnx91527
 */

#ifndef SRC_BUFFERBUILDER_H_
#define SRC_BUFFERBUILDER_H_

#include "AsciiStackReader.h"
#include "DataWord.h"
#include <vector>

class BufferBuilder {
public:
	BufferBuilder(const std::string& dataPath, int packetsPerBuffer);
	virtual ~BufferBuilder();
	int build(int qtyBuffers = 1);
	void *getBufferPtr(int index);
	int getBufferWordCount();

private:
	AsciiStackReader *asr_;
	int qtyBuffers_;
	int wordsPerPacket_;
	int packetsPerBuffer_;
	std::vector<void *> buffers_;
};

#endif /* SRC_BUFFERBUILDER_H_ */
