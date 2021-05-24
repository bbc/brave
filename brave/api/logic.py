from brave.helpers import run_on_master_thread_when_idle

class Logic():

    @staticmethod
    def create_input(request):
        input = request['session'].inputs.add(**request.json)
        input.setup()
        # logger.info('Created input #%d with details %s' % (input.id, request.json))
        return request, input

    @staticmethod
    def create_output(request, input):
        output_uri = '/'.join(request.json['uri'].split("/")[:-2]) + "/live/" + request.json['uri'].split("/")[-1] + "0000" + str(input.id)
        params = {'type': 'rtmp', 'uri': output_uri, 'source': 'input' + str(input.id)} 
        request['session'].outputs.add(**params)
        return request

    def delete_input(input_content):
        run_on_master_thread_when_idle(input_content.delete)
    
    def delete_output(output_content):
        run_on_master_thread_when_idle(output_content.delete)
        