package com.binus.ootd;

import android.app.Application;
import android.content.Context;
import android.os.Build;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.Query;
import com.google.firebase.database.ValueEventListener;

import java.time.LocalDate;
import java.util.List;

public class EventAdaptor extends ArrayAdapter<Task> {
    private EventAdaptor adaptor;
    private CalenderAdaptor calenderadaptor;
    private LocalDate selectedDate;
    private List<Task> tasks;

    private FirebaseAuth mAuth;

    public EventAdaptor(@NonNull Context context, List<Task> tasks, CalenderAdaptor calenderadaptor, LocalDate selectedDate) {
        super(context, 0, tasks);
        this.adaptor = this;
        this.tasks = tasks;
        this.selectedDate = selectedDate;
        this.calenderadaptor = calenderadaptor;

        mAuth = FirebaseAuth.getInstance();
    }

    @NonNull
    @Override
    public View getView(int position, @NonNull View convertView, @NonNull ViewGroup parent){
        Task task = getItem(position);
        if(convertView == null)
            convertView = LayoutInflater.from(getContext()).inflate(R.layout.task_cell,parent, false);
        TextView task_cell = convertView.findViewById(R.id.task_cell);
        Button delete_task = convertView.findViewById(R.id.delete_task);
        String task_title = task.getTitle();
        task_cell.setText(task_title);

        delete_task.setOnClickListener(new View.OnClickListener() {
            @RequiresApi(api = Build.VERSION_CODES.O)
            @Override
            public void onClick(View view) {
                DatabaseReference taskReference = FirebaseDatabase.getInstance().getReference("tasks")
                        .child(mAuth.getUid()).child(selectedDate.toString()).child(task_title);
                taskReference.removeValue();

                adaptor.notifyDataSetChanged();
                calenderadaptor.notifyItemRangeRemoved(0, 42);
            }
        });
        return convertView;
    }


}
