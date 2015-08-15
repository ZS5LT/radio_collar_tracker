#include "FileWriter.hpp"
#include <queue>
#include "Sample.hpp"
#include <string>
#include <thread>
#include <mutex>
#include <fstream>
#include <cstdint>
#include <stdexcept>
extern "C"{
	#include <sys/stat.h>
	#include <limits.h>
}

using namespace std;

FileWriter::FileWriter(int sample_rate, SampleFactory* previous, int run_num)
		: sample_rate(sample_rate){
	this->run_num = run_num;
	this->previous_module = previous;
	this->run_state = true;
}

FileWriter::FileWriter(int sample_rate, SampleFactory* previous, string path,
		string data_prefix, string data_suffix, string meta_prefix,
		string meta_suffix, uint64_t block_length, int run_num){
	this->sample_rate = sample_rate;
	this->previous_module = previous;
	this->output_dir = path;
	this->data_prefix = data_prefix;
	this->data_suffix = data_suffix;
	this->meta_prefix = meta_prefix;
	this->meta_suffix = meta_suffix;
	this->block_length = block_length;
	this->run_num = run_num;

	// check args
	struct stat sb;
	if(stat(output_dir.c_str(), &sb)){
		// XXX ERROR
		throw invalid_argument("Could not stat directory!");
	}
	if(!S_ISDIR(sb.st_mode)){
		throw invalid_argument("Directory not a directory!");
	}
	run_state = true;
}

void FileWriter::start(){
	class_thread = new thread(&FileWriter::run, this);
}

void FileWriter::run(){
	// TODO initialize file
	ofstream fout;
	char sbuf[2];
	char fname_buf[PATH_MAX + NAME_MAX];
	uint64_t file_len = 0;
	int file_num = 1;

	sprintf(fname_buf, "%s/%s%06d_%06d%s", output_dir.c_str(),
			data_prefix.c_str(), run_num, file_num, data_suffix.c_str());
	fout.open(fname_buf, ios::out | ios::binary);
	if(fout.bad()){
		// TODO throw something
	}
	while(run_state){
		CRFSample* sample = previous_module->getNextSample();
		if(!sample){
			// TODO wait if necessary
			continue;
		}
		if(sample->isTerminating()){
			break;
		}
		sbuf[0] = sample->getData().real();
		sbuf[1] = sample->getData().imag();
		if(file_len + 2 * sizeof(float) > block_length){
			// TODO update file
			fout.close();
			sprintf(fname_buf, "%s/%s%06d_%06d%s", output_dir.c_str(),
					data_prefix.c_str(), run_num, file_num,
					data_suffix.c_str());
			fout.open(fname_buf, ios::out | ios::binary);
			file_len = 0;
		}
		fout.write(reinterpret_cast<char*>(sbuf), 2 * sizeof(float));
		file_len += 2 * sizeof(float);
	}
	fout.close();

	// Meta file
	sprintf(fname_buf, "%s/%s%06d%s", output_dir.c_str(), meta_prefix.c_str(),
			run_num, meta_suffix.c_str());
	fout.open(fname_buf, ios::out);
	fout << "sample_rate: " << sample_rate << endl;
	fout.close();
}


FileWriter::~FileWriter(){
	run_state = false;
	if(class_thread){
		class_thread->join();
	}
}

void FileWriter::setMetaPrefix(string str){
	this->meta_prefix = str;
}

void FileWriter::setMetaSuffix(string str){
	this->meta_suffix = str;
}

void FileWriter::setDataPrefix(string str){
	this->data_prefix = str;
}

void FileWriter::setDataSuffix(string str){
	this->data_suffix = str;
}

void FileWriter::setDataDir(string str){
	struct stat sb;
	if(stat(str.c_str(), &sb)){
		throw invalid_argument("Could not stat directory!");
	}
	if(!S_ISDIR(sb.st_mode)){
		throw invalid_argument("Directory not a directory!");
	}
	this->output_dir = str;
}

void FileWriter::setBlockLength(uint64_t len){
	this->block_length = len;
}
