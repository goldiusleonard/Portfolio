package com.binus.ootd;

import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class YourTaskActivity extends AppCompatActivity implements CalenderAdaptor.OnItemListener {
    private TextView monthYearText, noYourTaskText;
    private RecyclerView calenderRecyclerView;
    public static LocalDate selectedDate;
    private ListView list_task;
    private CalenderAdaptor calenderAdaptor;

    private FirebaseDatabase rootNode;
    private DatabaseReference todayTaskReference;
    private FirebaseUser user;

    private FirebaseAuth mAuth;

    @RequiresApi(api = Build.VERSION_CODES.O)
    @Override
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_your_task);
        initWidgets();
        selectedDate = LocalDate.now();

        mAuth = FirebaseAuth.getInstance();
        rootNode = FirebaseDatabase.getInstance();

        user = mAuth.getCurrentUser();
        todayTaskReference = rootNode.getReference("tasks").child(user.getUid()).child(selectedDate.toString());

        setMonthView();
    }

    private void initWidgets() {
        calenderRecyclerView = findViewById(R.id.calender_recyclerview);
        monthYearText = findViewById(R.id.weekly_task);
        list_task = findViewById(R.id.list_task);
        noYourTaskText = findViewById(R.id.no_your_task_text);
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    private void setMonthView() {
        monthYearText.setText(monthYearFromDate(selectedDate));
        ArrayList<LocalDate> daysInMonth = daysInMonthArray(selectedDate);

        calenderAdaptor = new CalenderAdaptor(daysInMonth, user.getUid(), this,getApplication());
        RecyclerView.LayoutManager layoutManager = new GridLayoutManager(getApplicationContext(),7);
        calenderRecyclerView.setLayoutManager(layoutManager);
        calenderRecyclerView.setAdapter(calenderAdaptor);
        setEventAdaptor();

    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    public ArrayList<LocalDate> daysInMonthArray(LocalDate date) {
        ArrayList<LocalDate> daysInMonthArray = new ArrayList<>();
        YearMonth yearMonth = YearMonth.from(date);
        int daysInMonth = yearMonth.lengthOfMonth();
        LocalDate fistOfMonth = selectedDate.withDayOfMonth(1);
        int dayOfWeek = fistOfMonth.getDayOfWeek().getValue();

        todayTaskReference = rootNode.getReference("tasks").child(user.getUid()).child(selectedDate.toString());
        ValueEventListener postListener = new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot dataSnapshot) {
                 long count = dataSnapshot.getChildrenCount();

                 if(count <= 0) {
                     noYourTaskText.setVisibility(View.VISIBLE);
                     list_task.setVisibility(View.GONE);
                 }
                 else {
                     noYourTaskText.setVisibility(View.GONE);
                     list_task.setVisibility(View.VISIBLE);
                 }
            }

            @Override
            public void onCancelled(DatabaseError databaseError) {

            }
        };
        todayTaskReference.addValueEventListener(postListener);

        for(int i=1; i<42 ;i++){
            if(i<=dayOfWeek||i>daysInMonth + dayOfWeek){
                daysInMonthArray.add(null);
            }
            else{
                daysInMonthArray.add(LocalDate.of(selectedDate.getYear(), selectedDate.getMonth(), i-dayOfWeek));
            }
        }
        return daysInMonthArray;
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    public static String monthYearFromDate(LocalDate date){
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMM yyyy");
        return date.format(formatter);
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    public void next_month(View view){
        selectedDate = selectedDate.plusMonths(1);
        setMonthView();
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    public void prev_month(View view){
        selectedDate = selectedDate.minusMonths(1);
        setMonthView();
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    @Override
    public void onItemClick(int position, LocalDate date) {
        if(date != null){
            selectedDate = date;
            setMonthView();
        }
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    @Override
    protected void onResume() {

        super.onResume();
        setEventAdaptor();
    }

    @RequiresApi(api = Build.VERSION_CODES.O)
    private void setEventAdaptor() {
        todayTaskReference = rootNode.getReference("tasks").child(user.getUid()).child(selectedDate.toString());

        ValueEventListener postListener = new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot dataSnapshot) {
                Iterable<DataSnapshot> taskList = dataSnapshot.getChildren();
                ArrayList<Task> dailyTasks = new ArrayList<>();

                for(DataSnapshot task:taskList) {
                    dailyTasks.add(new Task(task.getKey()));
                }
                EventAdaptor eventAdaptor = new EventAdaptor(getApplicationContext(), dailyTasks, calenderAdaptor, selectedDate);
                list_task.setAdapter(eventAdaptor);
            }

            @Override
            public void onCancelled(DatabaseError databaseError) {

            }
        };
        todayTaskReference.addValueEventListener(postListener);
    }


    @RequiresApi(api = Build.VERSION_CODES.O)
    public void NewEvent(View view) {
        startActivity(new Intent(this,EventEditActivity.class));
    }

    public void back(View view) {
        startActivity(new Intent(this, HomeActivity.class));
        finish();
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        startActivity(new Intent(this, HomeActivity.class));
        finish();
    }
}
